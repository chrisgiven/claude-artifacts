# ADR-001: Platform architecture

**Status:** Accepted (v0.2)  **Date:** 2026-10-28

## Context
The v0.1 prototype hard-coded each scenario in Python and only ran on Docker. The enterprise build (BUILD_PROMPT.md) needs the same drill, measurement and evidence on Azure ASR, AWS DRS and VMware tooling. It also needs scenarios that non-developers can review.

## Decision
Split the platform into a platform-neutral engine and per-platform providers.

```
scenarios/*.yaml ──► scenario.py (schema + validation against the provider's actions)
twin.yaml ─────────► engine.py
                        1. provider.up()               build twin from recovery artifacts
                        2. provider.isolation_proof()  GATE: fail closed
                        3. drift.check()               GATE: fail closed
                        4. load.Load                   sequenced synthetic writes
                        5. fault steps → runbook steps (each timed, actor-tagged, status-tracked)
                        6. measure.py                  RTO/RPO from the client's view
                        7. provider.teardown()         kill switch + attestation
                     ──► evidence.py  results.json · scorecard.html · history.jsonl · trend.html
providers/
  base.py    contract: up · isolation_proof · inventory · teardown · actions
  docker.py  reference implementation (local Docker)
  azure.py   next: ASR test failover into an isolated VNet
```

## Rules
- **Gates fail closed.** No fault is injected unless the isolation proof and the drift check both pass.
- **Scenarios are data.** A scenario may only use actions its provider declares, and validation runs at load time. Adding a platform means implementing the same action names (`kill`, `promote`, `restore_backup` ...) against that platform's API.
- **Measurement is provider-agnostic.** RTO/RPO come only from the synthetic client's records and the set of surviving sequence numbers. Providers cannot report their own RTO.
- **Every run tears down and attests**, unless `--keep` is passed. The attestation lists residual objects.

## Consequences
- Azure, AWS and VMware work is limited to the provider module plus a twin manifest. The engine, scenarios and evidence don't change.
- Human decision time is still simulated (`declare` sleeps). Replacing it with an operator console is on the roadmap.
