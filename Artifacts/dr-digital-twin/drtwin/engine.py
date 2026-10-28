"""Drill lifecycle: build -> prove isolation -> check drift -> load -> fault ->
runbook -> measure. Gates fail closed: no fault is injected unless the
isolation proof and the drift check both pass."""
import time
import traceback

from drtwin import drift
from drtwin.load import Load
from drtwin.measure import grade, measure


class GateFailed(RuntimeError):
    pass


def run_steps(steps, actions, ctx, log, deadline):
    for step in steps:
        rec = {"name": step.name, "actor": step.actor, "action": step.action, "start": time.time()}
        log.append(rec)
        try:
            if time.time() > deadline:
                raise TimeoutError("stop condition: scenario exceeded max_duration_s")
            detail = actions[step.action](step.args, ctx)
            rec["status"] = "ok"
            if detail:
                rec["detail"] = detail
        except Exception as e:
            rec["status"] = "failed"
            rec["detail"] = f"{type(e).__name__}: {e}"[:300]
            return False
        finally:
            rec["end"] = time.time()
    return True


def drill(scenario, provider, client, opts, say=print):
    say(f"\n=== {scenario.id}: {scenario.title}")
    started = time.time()
    provider.up(client.healthy)

    iso = provider.isolation_proof()
    say(f"    isolation proof: {'PASS' if iso['passed'] else 'FAIL'}")
    if not iso["passed"]:
        raise GateFailed(f"isolation proof failed: {iso['checks']}")

    fidelity = drift.check(provider.manifest["expected"], provider.inventory())
    say(f"    drift check:     {'PASS' if fidelity['passed'] else 'FAIL'}")
    if not fidelity["passed"]:
        raise GateFailed(f"drift check failed: {[c for c in fidelity['checks'] if not c['passed']]}")

    load = Load(client, opts.rate)
    load.start()
    time.sleep(scenario.warmup_s or opts.warmup)

    actions, log = provider.actions(), []
    t0 = time.time()
    ctx = {"t0": t0, "declare_delay": opts.declare_delay, "healthy": client.healthy}
    deadline = t0 + scenario.max_duration_s
    completed = (run_steps(scenario.fault, actions, ctx, log, deadline)
                 and run_steps(scenario.runbook, actions, ctx, log, deadline))
    time.sleep(opts.cooldown)
    load.stop()

    try:
        surviving = client.surviving_seqs()
    except RuntimeError:
        surviving = set()
        completed = False
    m = measure(load.records, t0, surviving)
    m.update(grade(m, scenario.targets))
    rb = [s for s in log if s["actor"] != "inject"]
    m["runbook_accuracy_pct"] = round(100 * sum(s["status"] == "ok" for s in rb) / len(rb)) if rb else 100
    m["completed"] = completed
    say(f"    RTO {m['rto_s']}s (target {scenario.targets['rto_s']}s)  "
        f"RPO {m['rpo_s']}s (target {scenario.targets['rpo_s']}s)  "
        f"lost acked writes {m['lost_acked_writes']}  runbook {m['runbook_accuracy_pct']}%")

    return {
        "scenario": scenario.id, "title": scenario.title, "tier": scenario.tier,
        "description": scenario.description, "targets": scenario.targets,
        "provider": provider.name, "started": started, "t0": t0,
        "isolation": iso, "drift": fidelity, "metrics": m,
        "runbook": [{**s, "start": round(s["start"] - t0, 1), "end": round(s["end"] - t0, 1)} for s in log],
        "timeline": [{"t": round(r["t"] - t0, 2), "ok": r["ok"], "site": r["site"]} for r in load.records],
    }


def run_all(scenarios, provider, client, opts, say=print):
    results, errors = [], []
    try:
        for sc in scenarios:
            try:
                results.append(drill(sc, provider, client, opts, say))
            except GateFailed as e:
                say(f"    ABORTED (gate): {e}")
                errors.append({"scenario": sc.id, "error": str(e), "kind": "gate"})
            except Exception as e:
                say(f"    ERROR: {e}")
                errors.append({"scenario": sc.id, "error": str(e), "kind": "error",
                               "trace": traceback.format_exc()[-2000:]})
    finally:
        attestation = None if opts.keep else provider.teardown()
    return results, errors, attestation
