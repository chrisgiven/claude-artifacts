#!/usr/bin/env python3
"""DR drill harness for the digital twin.

For each scenario: rebuild the twin from scratch, prove isolation, run steady
load, inject the fault, execute the recovery runbook with timestamped steps,
then measure RTO/RPO from the client's point of view and write a scorecard.

Stdlib only. Usage:
    python3 harness/drill.py                  # all scenarios
    python3 harness/drill.py ha-db-primary    # one scenario
    python3 harness/drill.py --declare-delay 30 --build
"""
import argparse
import html
import json
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = json.loads((ROOT / "harness" / "scenarios.json").read_text())
STABLE_OKS = 5  # consecutive successful writes that count as "recovered"


# ---------------------------------------------------------------- plumbing

def sh(*args, check=True, timeout=180):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{r.stderr.strip()}")
    return r


def compose(*args, **kw):
    return sh("docker", "compose", *args, **kw)


def psql(service, sql, check=True):
    return compose("exec", "-T", service, "psql", "-U", "postgres", "-d", "orders",
                   "-tAc", sql, check=check).stdout.strip()


def wait_for(desc, fn, timeout=120, interval=1.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if fn():
                return
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for: {desc}")


class Twin:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"

    def call(self, method, path, timeout=5):
        req = urllib.request.Request(self.base + path, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception:
            return 0, {}

    def healthy(self):
        return self.call("GET", "/health")[0] == 200


# ---------------------------------------------------------------- load

class Load(threading.Thread):
    """Steady write traffic; every request is recorded with its outcome."""

    def __init__(self, twin, rate):
        super().__init__(daemon=True)
        self.twin, self.gap = twin, 1.0 / rate
        self.records, self.stop_flag, self.seq = [], threading.Event(), 0

    def run(self):
        while not self.stop_flag.is_set():
            self.seq += 1
            t = time.time()
            code, body = self.twin.call("POST", f"/orders?seq={self.seq}", timeout=6)
            self.records.append({"seq": self.seq, "t": t, "ok": code == 200,
                                 "code": code, "site": body.get("site"),
                                 "lat_ms": round((time.time() - t) * 1000)})
            time.sleep(max(0, self.gap - (time.time() - t)))

    def stop(self):
        self.stop_flag.set()
        self.join()


# ---------------------------------------------------------------- runbook

class Runbook:
    def __init__(self):
        self.steps = []

    def step(self, name, actor, fn=None):
        s = {"name": name, "actor": actor, "start": time.time()}
        result = fn() if fn else None
        s["end"] = time.time()
        if isinstance(result, str):
            s["detail"] = result
        self.steps.append(s)
        return result


def latest_clean_backup(before_ts):
    names = compose("exec", "-T", "backup", "ls", "/vault").stdout.split()
    stamps = sorted(int(n[7:-5]) for n in names if n.startswith("orders-") and n.endswith(".dump"))
    clean = [s for s in stamps if s < before_ts]
    if not clean:
        raise RuntimeError("no backup older than the incident: unrecoverable")
    return clean[-1]


def promote_dr_db():
    psql("pg-b", "SELECT pg_promote(true, 60)")
    return "pg-b promoted to primary"


def run_scenario(name, twin, rb, args):
    """Inject the fault and run the recovery runbook. Returns injection time."""
    declare = lambda: time.sleep(args.declare_delay)
    declare_label = f"Declare incident (simulated human decision, {args.declare_delay:.0f}s)"
    wait_healthy = lambda: wait_for("service healthy via LB", twin.healthy, timeout=180)

    if name == "ha-app-node":
        t0 = time.time()
        compose("kill", "app-a1")
        rb.step("Fault: app-a1 lost", "inject")
        rb.step("LB health check removes node (no human action)", "auto", wait_healthy)
        return t0

    if name == "ha-db-primary":
        t0 = time.time()
        compose("kill", "pg-a")
        rb.step("Fault: primary database pg-a lost", "inject")
        rb.step(declare_label, "human", declare)
        rb.step("Promote standby pg-b", "runbook", promote_dr_db)
        rb.step("Validate service via LB", "runbook", wait_healthy)
        return t0

    if name == "dr-site-a-loss":
        t0 = time.time()
        compose("kill", "app-a1", "app-a2", "pg-a")
        rb.step("Fault: site A lost (app-a1, app-a2, pg-a)", "inject")
        rb.step(declare_label, "human", declare)
        rb.step("Promote site B database pg-b", "runbook", promote_dr_db)
        rb.step("Validate site B serving via LB", "runbook", wait_healthy)
        return t0

    if name == "cyber-logical-corruption":
        t0 = time.time()
        psql("pg-a", "DROP TABLE orders CASCADE")
        rb.step("Fault: orders table destroyed on primary (replicates to DR)", "inject")
        rb.step(declare_label, "human", declare)
        rb.step("Contain: stop application tier", "runbook",
                lambda: compose("stop", "-t", "2", "app-a1", "app-a2", "app-b1") and None)
        bk = rb.step("Identify last clean restore point in vault", "runbook",
                     lambda: latest_clean_backup(t0))
        rb.steps[-1]["detail"] = f"orders-{bk}.dump ({t0 - bk:.0f}s before incident)"
        rb.step("Restore database from vault", "runbook", lambda: compose(
            "exec", "-T", "backup", "pg_restore", "--clean", "--if-exists",
            "-d", "host=pg-a dbname=orders user=postgres", f"/vault/orders-{bk}.dump") and None)
        rb.step("Restart application tier", "runbook",
                lambda: compose("start", "app-a1", "app-a2", "app-b1") and None)
        rb.step("Validate service via LB", "runbook", wait_healthy)
        return t0

    raise ValueError(f"unknown scenario {name}")


# ---------------------------------------------------------------- measure

def measure(records, t0, surviving):
    after = [r for r in records if r["t"] >= t0]
    first_fail = next((r for r in after if not r["ok"]), None)
    recovered_at, streak = None, []
    for r in after:
        streak = streak + [r] if r["ok"] else []
        if len(streak) == STABLE_OKS and first_fail and r["t"] > first_fail["t"]:
            recovered_at = streak[0]["t"]
            break
    if first_fail is None:
        rto = 0.0
    elif recovered_at is None:
        rto = None  # never recovered within the observation window
    else:
        rto = recovered_at - t0

    # RPO: span from the last write that survived to the last acknowledged
    # write that did not. Zero when every acknowledged write survived.
    acked = [r for r in records if r["ok"]]
    lost = [r for r in acked if r["seq"] not in surviving]
    rpo = 0.0
    if lost:
        kept = [r["t"] for r in acked if r["seq"] in surviving and r["t"] < lost[0]["t"]]
        rpo = lost[-1]["t"] - (max(kept) if kept else lost[0]["t"])
    failed = [r for r in after if not r["ok"]]
    return {
        "rto_s": None if rto is None else round(rto, 1),
        "rpo_s": round(rpo, 1),
        "time_to_impact_s": round(first_fail["t"] - t0, 1) if first_fail else None,
        "failed_requests": len(failed),
        "acked_writes": len(acked),
        "lost_acked_writes": len(lost),
        "serving_site_after": next((r["site"] for r in reversed(records) if r["ok"]), None),
    }


# ---------------------------------------------------------------- lifecycle

def build_twin(args):
    compose("down", "-v", "--remove-orphans", check=False)
    compose("up", "-d", *(["--build"] if args.build else []), timeout=600)
    twin = Twin(args.port)
    wait_for("LB healthy", twin.healthy, timeout=120)
    wait_for("pg-b streaming from pg-a", lambda: psql(
        "pg-a", "SELECT count(*) FROM pg_stat_replication WHERE state='streaming'") == "1")
    wait_for("first backup in vault", lambda: "orders-" in compose(
        "exec", "-T", "backup", "ls", "/vault").stdout, timeout=90)
    return twin


def prove_isolation():
    """The twin must have no egress: no internet, no DNS, no path to production."""
    probe = ("import socket,sys\n"
             "for h,p in [('1.1.1.1',443),('8.8.8.8',53)]:\n"
             "  s=socket.socket();s.settimeout(3)\n"
             "  try: s.connect((h,p)); print('REACHED',h); sys.exit(1)\n"
             "  except OSError: pass\n"
             "try: socket.gethostbyname('example.com'); print('DNS LEAK'); sys.exit(1)\n"
             "except OSError: pass\n")
    r = compose("exec", "-T", "app-a1", "python", "-c", probe, check=False)
    return {"passed": r.returncode == 0, "detail": (r.stdout + r.stderr).strip() or "no egress, no external DNS"}


def drill(name, args):
    spec = SCENARIOS[name]
    print(f"\n=== {name}: {spec['title']}")
    twin = build_twin(args)
    iso = prove_isolation()
    print(f"    isolation proof: {'PASS' if iso['passed'] else 'FAIL'}")
    if not iso["passed"]:
        raise SystemExit("isolation proof failed; refusing to run fault injection")

    load = Load(twin, args.rate)
    load.start()
    time.sleep(spec.get("warmup_s", args.warmup))
    rb = Runbook()
    t0 = run_scenario(name, twin, rb, args)
    time.sleep(args.cooldown)
    load.stop()

    code, body = twin.call("GET", "/orders/seqs", timeout=10)
    if code != 200:
        raise RuntimeError("could not read surviving orders after recovery")
    m = measure(load.records, t0, set(body["seqs"]))
    t = spec["targets"]
    m["rto_pass"] = m["rto_s"] is not None and m["rto_s"] <= t["rto_s"]
    m["rpo_pass"] = m["rpo_s"] <= t["rpo_s"]
    print(f"    RTO {m['rto_s']}s (target {t['rto_s']}s)  RPO {m['rpo_s']}s (target {t['rpo_s']}s)  "
          f"lost acked writes {m['lost_acked_writes']}")
    return {"scenario": name, **spec, "t0": t0, "isolation": iso, "metrics": m,
            "runbook": [{**s, "start": round(s["start"] - t0, 1), "end": round(s["end"] - t0, 1)}
                        for s in rb.steps],
            "timeline": [{"t": round(r["t"] - t0, 2), "ok": r["ok"], "site": r["site"]}
                         for r in load.records]}


# ---------------------------------------------------------------- report

def strip_svg(timeline, width=720, height=28):
    if not timeline:
        return ""
    lo, hi = timeline[0]["t"], timeline[-1]["t"]
    span = (hi - lo) or 1
    x = lambda t: (t - lo) / span * width
    bars = "".join(
        f'<rect x="{x(r["t"]):.1f}" y="0" width="{max(width / len(timeline), 1):.1f}" '
        f'height="{height}" class="{"ok" if r["ok"] else "bad"}"/>' for r in timeline)
    marker = f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="0" y2="{height}" class="t0"/>'
    return (f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" '
            f'aria-label="Write success over time">{bars}{marker}</svg>'
            f'<div class="axis"><span>{lo:.0f}s</span><span>fault at 0s</span><span>+{hi:.0f}s</span></div>')


def fmt(v, unit="s"):
    return "—" if v is None else f"{v}{unit}"


def write_report(results, args):
    out = ROOT / "reports" / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2))

    rows, sections = [], []
    for r in results:
        m, t = r["metrics"], r["targets"]
        badge = lambda ok: f'<span class="b {"pass" if ok else "fail"}">{"PASS" if ok else "FAIL"}</span>'
        rows.append(
            f"<tr><td>{html.escape(r['title'])}</td><td>{r['tier']}</td>"
            f"<td class=n>{t['rto_s']}s</td><td class=n>{fmt(m['rto_s'])}</td><td>{badge(m['rto_pass'])}</td>"
            f"<td class=n>{t['rpo_s']}s</td><td class=n>{fmt(m['rpo_s'])}</td><td>{badge(m['rpo_pass'])}</td>"
            f"<td class=n>{m['lost_acked_writes']}</td></tr>")
        steps = "".join(
            f"<tr><td class=n>+{s['start']}s</td><td class=n>{s['end'] - s['start']:.1f}s</td>"
            f"<td>{s['actor']}</td><td>{html.escape(s['name'])}"
            f"{' — ' + html.escape(s['detail']) if s.get('detail') else ''}</td></tr>" for s in r["runbook"])
        sections.append(f"""
<section><h2>{html.escape(r['title'])}</h2><p class=muted>{html.escape(r['description'])}</p>
<div class=kpis>
 <div><b>{fmt(m['rto_s'])}</b><span>Measured RTO</span></div>
 <div><b>{fmt(m['rpo_s'])}</b><span>Measured RPO</span></div>
 <div><b>{m['failed_requests']}</b><span>Failed requests</span></div>
 <div><b>{m['lost_acked_writes']}</b><span>Lost acknowledged writes</span></div>
 <div><b>{m['serving_site_after'] or '—'}</b><span>Serving site after</span></div>
</div>
<h3>Client view (each bar = one write)</h3>{strip_svg(r['timeline'])}
<h3>Runbook timeline</h3>
<table><thead><tr><th>Start</th><th>Duration</th><th>Actor</th><th>Step</th></tr></thead><tbody>{steps}</tbody></table>
<p class=muted>Isolation proof: {'PASS' if r['isolation']['passed'] else 'FAIL'} — {html.escape(r['isolation']['detail'])}</p>
</section>""")

    page = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>DR Drill Scorecard</title>
<style>
:root{{--bg:#fff;--fg:#1a1d21;--mut:#5b6470;--line:#e2e5e9;--ok:#2e8540;--bad:#c62828;--card:#f6f7f9}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161a;--fg:#e8eaed;--mut:#9aa3ad;--line:#2b3037;--ok:#4caf50;--bad:#ef5350;--card:#1c1f24}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:24px 16px}}
h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:17px;margin:32px 0 4px}}h3{{font-size:13px;color:var(--mut);margin:18px 0 6px;text-transform:uppercase;letter-spacing:.04em}}
.muted{{color:var(--mut)}}table{{border-collapse:collapse;width:100%;display:block;overflow-x:auto}}
th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;white-space:nowrap}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.b{{font-size:11px;font-weight:600;padding:2px 6px;border-radius:4px;color:#fff}}.pass{{background:var(--ok)}}.fail{{background:var(--bad)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-top:12px}}
.kpis div{{background:var(--card);border-radius:8px;padding:10px}}.kpis b{{display:block;font-size:20px}}.kpis span{{color:var(--mut);font-size:12px}}
svg{{width:100%;height:28px;display:block;border-radius:4px}}rect.ok{{fill:var(--ok)}}rect.bad{{fill:var(--bad)}}line.t0{{stroke:var(--fg);stroke-width:2}}
.axis{{display:flex;justify-content:space-between;color:var(--mut);font-size:11px}}
</style></head><body>
<h1>DR Drill Scorecard</h1>
<p class=muted>{datetime.now():%Y-%m-%d %H:%M} · load {args.rate}/s · declare delay {args.declare_delay:.0f}s (simulated) · recovery = {STABLE_OKS} consecutive successful writes</p>
<table><thead><tr><th>Scenario</th><th>Tier</th><th>RTO target</th><th>RTO actual</th><th></th>
<th>RPO target</th><th>RPO actual</th><th></th><th>Lost writes</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
{''.join(sections)}
</body></html>"""
    (out / "scorecard.html").write_text(page)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenarios", nargs="*", help=f"default: all ({', '.join(SCENARIOS)})")
    p.add_argument("--rate", type=float, default=10, help="writes per second (default 10)")
    p.add_argument("--declare-delay", type=float, default=15, help="simulated human decision time, seconds")
    p.add_argument("--warmup", type=float, default=10)
    p.add_argument("--cooldown", type=float, default=10)
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--build", action="store_true", help="rebuild the app image")
    p.add_argument("--keep", action="store_true", help="leave the twin running after the last drill")
    args = p.parse_args()
    unknown = set(args.scenarios) - set(SCENARIOS)
    if unknown:
        p.error(f"unknown scenario(s): {', '.join(sorted(unknown))}")
    args.scenarios = args.scenarios or list(SCENARIOS)

    results = []
    try:
        for name in args.scenarios:
            results.append(drill(name, args))
    finally:
        if results:
            print(f"\nScorecard: {write_report(results, args) / 'scorecard.html'}")
        if not args.keep:
            compose("down", "-v", "--remove-orphans", check=False)


if __name__ == "__main__":
    main()
