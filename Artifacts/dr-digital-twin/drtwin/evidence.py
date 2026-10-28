"""Evidence pack: results.json, scorecard.html, attestation, and drill history."""
import html
import json
from datetime import datetime
from pathlib import Path

from drtwin.measure import STABLE_OKS

CSS = """
:root{--bg:#fff;--fg:#1a1d21;--mut:#5b6470;--line:#e2e5e9;--ok:#2e8540;--bad:#c62828;--card:#f6f7f9}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#e8eaed;--mut:#9aa3ad;--line:#2b3037;--ok:#4caf50;--bad:#ef5350;--card:#1c1f24}}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 4px}
h3{font-size:13px;color:var(--mut);margin:18px 0 6px;text-transform:uppercase;letter-spacing:.04em}
.muted{color:var(--mut)}table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;white-space:nowrap}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.b{font-size:11px;font-weight:600;padding:2px 6px;border-radius:4px;color:#fff}.pass{background:var(--ok)}.fail{background:var(--bad)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-top:12px}
.kpis div{background:var(--card);border-radius:8px;padding:10px}.kpis b{display:block;font-size:20px}.kpis span{color:var(--mut);font-size:12px}
svg{width:100%;height:28px;display:block;border-radius:4px}rect.ok{fill:var(--ok)}rect.bad{fill:var(--bad)}line.t0{stroke:var(--fg);stroke-width:2}
.axis{display:flex;justify-content:space-between;color:var(--mut);font-size:11px}
"""


def esc(v):
    return html.escape(str(v))


def badge(ok):
    return f'<span class="b {"pass" if ok else "fail"}">{"PASS" if ok else "FAIL"}</span>'


def fmt(v, unit="s"):
    return "—" if v is None else f"{v}{unit}"


def page(title, body):
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{esc(title)}</title><style>{CSS}</style></head><body>{body}</body></html>")


def strip_svg(timeline, width=720, height=28):
    if not timeline:
        return ""
    # Merge consecutive same-outcome requests into one rect to keep the file small.
    lo, hi = timeline[0]["t"], timeline[-1]["t"]
    span = (hi - lo) or 1
    x = lambda t: (t - lo) / span * width
    runs, start = [], 0
    for i in range(1, len(timeline) + 1):
        if i == len(timeline) or timeline[i]["ok"] != timeline[start]["ok"]:
            end_t = timeline[i]["t"] if i < len(timeline) else hi
            runs.append((timeline[start]["t"], end_t, timeline[start]["ok"]))
            start = i
    bars = "".join(f'<rect x="{x(a):.1f}" y="0" width="{max(x(b) - x(a), 1):.1f}" height="{height}" '
                   f'class="{"ok" if ok else "bad"}"/>' for a, b, ok in runs)
    marker = f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="0" y2="{height}" class="t0"/>'
    return (f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" '
            f'aria-label="Write success over time">{bars}{marker}</svg>'
            f'<div class="axis"><span>{lo:.0f}s</span><span>fault at 0s</span><span>+{hi:.0f}s</span></div>')


def checks_table(checks):
    rows = "".join(f"<tr><td>{badge(c['passed'])}</td><td>{esc(c['check'])}</td>"
                   f"<td class=muted>{esc(c.get('detail', ''))}</td></tr>" for c in checks)
    return f"<table><tbody>{rows}</tbody></table>"


def scenario_section(r):
    m = r["metrics"]
    steps = "".join(
        f"<tr><td>{badge(s['status'] == 'ok')}</td><td class=n>+{s['start']}s</td>"
        f"<td class=n>{s['end'] - s['start']:.1f}s</td><td>{esc(s['actor'])}</td>"
        f"<td>{esc(s['name'])}{' — ' + esc(s['detail']) if s.get('detail') else ''}</td></tr>"
        for s in r["runbook"])
    return f"""
<section><h2>{esc(r['title'])}</h2><p class=muted>{esc(r['description'])}</p>
<div class=kpis>
 <div><b>{fmt(m['rto_s'])}</b><span>Measured RTO (target {r['targets']['rto_s']}s)</span></div>
 <div><b>{fmt(m['rpo_s'])}</b><span>Measured RPO (target {r['targets']['rpo_s']}s)</span></div>
 <div><b>{m['lost_acked_writes']}</b><span>Lost acknowledged writes</span></div>
 <div><b>{m['runbook_accuracy_pct']}%</b><span>Runbook accuracy</span></div>
 <div><b>{esc(m['serving_site_after'] or '—')}</b><span>Serving site after</span></div>
</div>
<h3>Client view (green = write succeeded)</h3>{strip_svg(r['timeline'])}
<h3>Runbook timeline</h3>
<table><thead><tr><th></th><th>Start</th><th>Duration</th><th>Actor</th><th>Step</th></tr></thead><tbody>{steps}</tbody></table>
<h3>Isolation proof (probed from {esc(r['isolation'].get('probed_from', '?'))})</h3>{checks_table(r['isolation']['checks'])}
<h3>Drift / fidelity check</h3>{checks_table(r['drift']['checks'])}
</section>"""


def scorecard(results, errors, attestation, opts):
    rows = "".join(
        f"<tr><td>{esc(r['title'])}</td><td>{esc(r['tier'])}</td>"
        f"<td class=n>{r['targets']['rto_s']}s</td><td class=n>{fmt(r['metrics']['rto_s'])}</td><td>{badge(r['metrics']['rto_pass'])}</td>"
        f"<td class=n>{r['targets']['rpo_s']}s</td><td class=n>{fmt(r['metrics']['rpo_s'])}</td><td>{badge(r['metrics']['rpo_pass'])}</td>"
        f"<td class=n>{r['metrics']['lost_acked_writes']}</td></tr>" for r in results)
    err = "".join(f"<tr><td>{esc(e['scenario'])}</td><td>{esc(e['kind'])}</td><td>{esc(e['error'])}</td></tr>"
                  for e in errors)
    err_html = f"<h2>Aborted drills</h2><table><tbody>{err}</tbody></table>" if errors else ""
    if attestation is None:
        att = "<p class=muted>Twin left running (--keep). No teardown attestation.</p>"
    else:
        left = ", ".join(f"{k}: {len(v)}" for k, v in attestation["residual"].items())
        att = (f"<p>{badge(attestation['destroyed'])} Twin <code>{esc(attestation['project'])}</code> destroyed "
               f"and verified at {datetime.fromtimestamp(attestation['verified_at']):%Y-%m-%d %H:%M:%S}. "
               f"Residual objects — {esc(left)}.</p>")
    body = f"""
<h1>DR Drill Scorecard</h1>
<p class=muted>{datetime.now():%Y-%m-%d %H:%M} · provider {esc(opts.provider)} · load {opts.rate}/s ·
declare delay {opts.declare_delay:.0f}s (simulated) · recovery = {STABLE_OKS} consecutive successful writes</p>
<table><thead><tr><th>Scenario</th><th>Tier</th><th>RTO target</th><th>RTO actual</th><th></th>
<th>RPO target</th><th>RPO actual</th><th></th><th>Lost writes</th></tr></thead><tbody>{rows}</tbody></table>
{err_html}
<h2>Teardown attestation</h2>{att}
{''.join(scenario_section(r) for r in results)}"""
    return page("DR Drill Scorecard", body)


def write_pack(reports, results, errors, attestation, opts):
    out = Path(reports) / datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(
        {"results": results, "errors": errors, "attestation": attestation,
         "options": vars(opts)}, indent=2, default=str))
    (out / "scorecard.html").write_text(scorecard(results, errors, attestation, opts))
    with open(Path(reports) / "history.jsonl", "a") as h:
        for r in results:
            h.write(json.dumps({"run": out.name, "scenario": r["scenario"], "provider": r["provider"],
                                "targets": r["targets"], **{k: r["metrics"][k] for k in (
                                    "rto_s", "rpo_s", "lost_acked_writes", "runbook_accuracy_pct",
                                    "rto_pass", "rpo_pass")}}) + "\n")
    trend(reports)
    return out


def trend(reports):
    path = Path(reports) / "history.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []
    by = {}
    for r in rows:
        by.setdefault(r["scenario"], []).append(r)
    sections = []
    for sc, runs in sorted(by.items()):
        rtos = [r["rto_s"] for r in runs if r["rto_s"] is not None]
        spread = (f"{min(rtos)}–{max(rtos)}s" if rtos else "—")
        body = "".join(
            f"<tr><td>{esc(r['run'])}</td><td class=n>{fmt(r['rto_s'])}</td><td>{badge(r['rto_pass'])}</td>"
            f"<td class=n>{fmt(r['rpo_s'])}</td><td>{badge(r['rpo_pass'])}</td>"
            f"<td class=n>{r['lost_acked_writes']}</td><td class=n>{r['runbook_accuracy_pct']}%</td></tr>"
            for r in runs[-20:])
        sections.append(
            f"<h2>{esc(sc)}</h2><p class=muted>{len(runs)} runs · RTO range {spread} · "
            f"target RTO {runs[-1]['targets']['rto_s']}s / RPO {runs[-1]['targets']['rpo_s']}s</p>"
            f"<table><thead><tr><th>Run</th><th>RTO</th><th></th><th>RPO</th><th></th><th>Lost writes</th>"
            f"<th>Runbook</th></tr></thead><tbody>{body}</tbody></table>")
    (Path(reports) / "trend.html").write_text(page("DR Drill Trend", "<h1>DR Drill Trend</h1>" + "".join(sections)))
