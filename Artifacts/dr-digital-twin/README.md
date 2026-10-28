# DR digital twin platform (v0.2)

Stands up an isolated, production-faithful twin and gates every drill on an isolation proof and a drift check. It then injects failures, runs recovery runbooks and measures **actual RTO/RPO from the client's point of view**. Each run produces an evidence pack with a teardown attestation.

- Enterprise build brief: [BUILD_PROMPT.md](BUILD_PROMPT.md)
- Architecture: [docs/ADR-001-platform-architecture.md](docs/ADR-001-platform-architecture.md)
- What's next: [ROADMAP.md](ROADMAP.md)

## Run (local Docker)

Requires Docker with Compose v2, Python 3.10+ and PyYAML (`pip install -r requirements.txt`).

```bash
python3 -m drtwin list                              # scenarios and targets
python3 -m drtwin validate                          # schema-check scenarios
python3 -m drtwin run                               # all scenarios, ~6 min
python3 -m drtwin run dr-site-a-loss --declare-delay 60
python3 -m drtwin run --build                       # rebuild app image after code changes
python3 -m drtwin teardown                          # kill switch + attestation
python3 -m unittest discover -s tests -t .          # unit tests
```

Each run writes `reports/<timestamp>/` (`scorecard.html` and `results.json`), appends to `reports/history.jsonl` and refreshes `reports/trend.html`. The exit code is non-zero if any drill aborts or misses a target, so it can gate CI.

## Drill lifecycle

| Stage | What happens | Fails closed? |
|---|---|---|
| Build | The twin is rebuilt from scratch (`provider.up`) | — |
| Isolation proof | Probes from inside the twin to the internet and external DNS | Yes: no fault is injected |
| Drift check | Running twin vs `twin.yaml`: services, replication, backup age | Yes |
| Load | Sequenced synthetic writes through the LB | — |
| Fault + runbook | Steps from `scenarios/*.yaml`, each timed, actor-tagged and status-tracked | Stops at the first failed step or `max_duration_s` |
| Measure | RTO = fault → start of 5 consecutive successful writes; RPO = acknowledged writes missing afterwards | — |
| Teardown | `down -v`, then verifies no containers, volumes or networks remain | Attestation records any residual objects |

## Topology (Docker provider)

```
 host ──127.0.0.1:8080──► lb (GSLB stand-in, active health checks)
                           │            internal "bubble" network: no egress
          ┌────────────────┼──────────────────────┐
     Site A (primary)               Site B (DR)
     app-a1  app-a2                 app-b1 (warm standby, backup pool)
     pg-a  ──── streaming WAL ────► pg-b (hot standby)
                backup ──► vault (scheduled dumps)
```

## Scenarios

| Scenario | Fault | Recovery | Target RTO / RPO |
|---|---|---|---|
| `ha-app-node` | Kill one of two site A app nodes | LB routes around it automatically | 5s / 0s |
| `ha-db-primary` | Kill the primary DB | Declare → promote standby → validate | 60s / 0s |
| `dr-site-a-loss` | Kill all of site A | Declare → promote site B DB → site B app serves | 120s / 5s |
| `cyber-logical-corruption` | Drop the business table (it replicates to DR) | Declare → contain → choose a clean backup → restore → restart → validate | 300s / 30s |

To add a scenario, drop a YAML file in `scenarios/`, using the actions the provider declares: `kill`, `stop`, `start`, `sql`, `promote`, `declare`, `wait_healthy`, `find_clean_backup`, `restore_backup`. `validate` rejects unknown actions.

## Findings so far

- **Replication is not backup.** The cyber scenario destroys data on both sites in under a second. Only the vault recovers it, and the RPO is set by the backup interval.
- **Backups of corrupted data still succeed.** Choosing the restore point is a runbook step.
- **A dead primary slows every connection** (about 2s on DNS lookup), so health-check timeouts have to allow for it.
- **Human declaration time dominates RTO** outside automatic HA.

## Limits

The Docker provider runs on a single host, so "sites" are logical. Human decision time is simulated. There's no identity, DNS or PKI layer yet. See ROADMAP.md.
