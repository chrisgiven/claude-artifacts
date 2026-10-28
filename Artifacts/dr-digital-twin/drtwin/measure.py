"""RTO/RPO from the client's point of view."""

STABLE_OKS = 5  # consecutive successful writes that count as "recovered"


def measure(records, t0, surviving, stable_oks=STABLE_OKS):
    after = [r for r in records if r["t"] >= t0]
    first_fail = next((r for r in after if not r["ok"]), None)
    recovered_at, streak = None, 0
    for i, r in enumerate(after):
        streak = streak + 1 if r["ok"] else 0
        if streak == stable_oks and first_fail and r["t"] > first_fail["t"]:
            recovered_at = after[i - stable_oks + 1]["t"]
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

    return {
        "rto_s": None if rto is None else round(rto, 1),
        "rpo_s": round(rpo, 1),
        "time_to_impact_s": round(first_fail["t"] - t0, 1) if first_fail else None,
        "failed_requests": sum(1 for r in after if not r["ok"]),
        "acked_writes": len(acked),
        "lost_acked_writes": len(lost),
        "serving_site_after": next((r["site"] for r in reversed(records) if r["ok"]), None),
    }


def grade(metrics, targets):
    return {
        "rto_pass": metrics["rto_s"] is not None and metrics["rto_s"] <= targets["rto_s"],
        "rpo_pass": metrics["rpo_s"] <= targets["rpo_s"],
    }
