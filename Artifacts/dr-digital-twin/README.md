# DR digital twin: prototype

A laptop-scale reference design for DR testing with a digital twin. It runs a two-site "production" estate inside an isolated network, injects failures, runs recovery runbooks and measures **actual RTO/RPO from the client's point of view**. Results go into a scorecard.

The enterprise build brief is in [BUILD_PROMPT.md](BUILD_PROMPT.md).

## Run

Requires Docker with Compose v2 and Python 3.10+ (stdlib only).

```bash
python3 harness/drill.py                       # all four scenarios, ~6 min
python3 harness/drill.py dr-site-a-loss        # one scenario
python3 harness/drill.py --declare-delay 60    # model a slower human decision
python3 harness/drill.py --build               # rebuild the app image after code changes
```

Each scenario rebuilds the twin from scratch. The scorecard is written to `reports/<timestamp>/scorecard.html`, with raw data in `results.json`.

## Topology

```
 host ──127.0.0.1:8080──► lb (GSLB stand-in, active health checks)
                           │            internal "bubble" network: no egress
          ┌────────────────┼──────────────────────┐
     Site A (primary)               Site B (DR)
     app-a1  app-a2                 app-b1 (warm standby, backup pool)
     pg-a  ──── streaming WAL ────► pg-b (hot standby)
                backup ──► vault (scheduled dumps)
```

## How it maps to the process

| Process control | Prototype implementation |
|---|---|
| Isolated environment | `bubble` network is `internal: true`. Only the LB is reachable, and only from localhost |
| Isolation proof before every run | Probes from inside the twin to the internet and external DNS; aborts if any succeed |
| Production-like workload | Sequenced writes at a steady rate through the LB |
| Fault injection | `docker kill` (node, DB, whole site), destructive SQL (cyber) |
| Runbook with timed steps | Each step is timestamped and tagged `auto`, `human` or `runbook` |
| Human decision time | `--declare-delay` (simulated; in the real build an operator console times it) |
| Measured RTO | Fault injection → start of 5 consecutive successful writes |
| Measured RPO | Acknowledged writes missing after recovery: count and time window |
| Evidence pack | `scorecard.html` + `results.json` |
| Teardown | `docker compose down -v` after every scenario |

## Scenarios

| Scenario | Fault | Recovery | Target RTO / RPO |
|---|---|---|---|
| `ha-app-node` | Kill one of two site A app nodes | LB routes around it automatically | 5s / 0s |
| `ha-db-primary` | Kill the primary DB | Declare → promote standby → validate | 60s / 0s |
| `dr-site-a-loss` | Kill all of site A | Declare → promote site B DB → site B app serves | 120s / 5s |
| `cyber-logical-corruption` | Drop the business table (it replicates to DR) | Declare → contain → choose a clean backup → restore → restart → validate | 300s / 30s |

Edit targets in `harness/scenarios.json`. To add a scenario, add an entry there and a branch in `run_scenario()`.

## Findings the prototype surfaces

- **Replication is not backup.** The cyber scenario destroys data on both sites in under a second. Only the vault recovers it, and the RPO is set by the backup interval.
- **Backups of corrupted data still succeed.** Choosing the restore point is a runbook step, not a given.
- **A dead primary slows every connection.** After failover, each DB connection waits about 2s on the dead host's DNS lookup before trying the standby. Health-check timeouts have to allow for that, or the LB flaps the recovered nodes.
- **Human declaration time dominates RTO** for anything that isn't automatic HA. Measure it.

## Limits (prototype, not product)

A single Docker host, so "sites" are logical. The LB is a single point of failure. There's no identity, DNS or PKI layer. Data is synthetic. The enterprise build in BUILD_PROMPT.md addresses each of these.
