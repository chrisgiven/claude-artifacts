"""Fidelity check: is the twin still a faithful copy of what it claims to be?"""


def check(expected, observed):
    findings = []
    want, have = expected["services"], observed["services"]
    for svc in sorted(want.keys() - have.keys()):
        findings.append({"check": f"service {svc} present", "passed": False, "detail": "missing"})
    for svc in sorted(have.keys() - want.keys()):
        findings.append({"check": f"service {svc} expected", "passed": False, "detail": "not in manifest"})
    for svc in sorted(want.keys() & have.keys()):
        running = have[svc]["state"] == "running"
        findings.append({"check": f"service {svc} running", "passed": running,
                         "detail": f"{have[svc]['state']} ({have[svc]['image']})"})
    n = expected["replication"]["standbys"]
    findings.append({"check": f"replication: {n} streaming standby(s)",
                     "passed": observed["replication_standbys"] == n,
                     "detail": f"{observed['replication_standbys']} streaming"})
    age, limit = observed["backup_age_s"], expected["backup"]["max_age_s"]
    findings.append({"check": f"newest backup under {limit}s old",
                     "passed": age is not None and age <= limit, "detail": f"{age}s"})
    return {"passed": all(f["passed"] for f in findings), "checks": findings}
