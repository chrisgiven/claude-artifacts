# Roadmap

Maps to the delivery plan in BUILD_PROMPT.md.

| # | Increment | Status |
|---|---|---|
| 0.1 | Prototype: two-site Docker twin, hard-coded drills, scorecard | Done |
| 0.2 | Platform core: YAML scenarios, provider contract, isolation and drift gates, runbook accuracy, evidence pack, teardown attestation, trend history, unit tests | **Done** |
| 0.3 | Operator console: humans click Declare / Approve, so decision time is measured, not simulated | Next |
| 0.4 | Azure provider: ASR test failover into an isolated VNet, NSG deny-all egress isolation proof, Chaos Studio faults | Planned, needs a sandbox subscription |
| 0.5 | Identity-first twin: AD DC restore and FSMO seizure in the bubble; foundational scenarios (AD, DNS, PKI loss) | Planned |
| 0.6 | Discovery import: CMDB / service map to recovery-order graph | Planned |
| 0.7 | Evidence: PDF export, control-ID mapping (DORA, SOC 2, NYDFS), RACI and rules-of-engagement templates | Planned |

## Open decisions
- Fault-injection tooling per platform (Chaos Studio vs. scripted).
- Where evidence packs are stored long-term (immutable storage for audit).
