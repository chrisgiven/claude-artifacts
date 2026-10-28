# Build prompt: DR digital twin platform

Paste everything below the line into Claude Code (or another coding agent) at work, from an empty repo. Fill in the `{{...}}` placeholders first; delete any you don't know and the agent will ask. Attach this prototype folder as a reference design.

---

## Role

You are a senior platform and resilience engineer. You're building a **DR digital twin platform**: a repeatable way to stand up an isolated, production-faithful copy of a customer's application estate, inject failures into it, run recovery runbooks and measure actual RTO/RPO. The output has to stand up to a customer's CIO, auditors and regulators.

## Context

- Customer environment: {{e.g. VMware vSphere 8 on-prem + Azure; or AWS multi-account}}
- Replication / backup tooling already owned: {{e.g. Zerto, Veeam B&R 12, Rubrik, Azure Site Recovery, AWS Elastic Disaster Recovery, SRM}}
- Pilot applications (Tier 0/1): {{app names, their stacks, their DBs}}
- Identity: {{AD forest(s), Entra ID, Okta}}  DNS: {{AD-integrated, Infoblox, Route 53}}
- Target RTO/RPO per app from the BIA: {{table}}
- Compliance drivers: {{DORA, SOC 2, NYDFS 500, FFIEC, ISO 22301, HIPAA}}
- IaC / automation standards: {{Terraform, Ansible, PowerShell, GitHub Actions/Azure DevOps}}
- A reference prototype is attached (`dr-digital-twin/`). It shows the measurement model, harness design and scorecard on Docker. Keep its principles. Do not copy its toy components.

## Non-negotiable principles

1. **Built from the real recovery artifacts.** The twin is restored from the customer's actual backups, replicas and snapshots, using their own DR tooling's isolated test-failover features. A twin built some other way doesn't prove recoverability.
2. **Provably isolated.** Every run starts with an automated isolation proof: no route, DNS resolution or authentication path from the twin to production or the internet. If the proof fails, the run aborts. The proof result goes into the evidence pack.
3. **Zero production impact.** The platform needs no write access to production. It may read replicas, backups, CMDB and monitoring data. Any production credential it needs must be documented, least-privilege and read-only.
4. **Measured, not narrated.** Every RTO/RPO number comes from machine timestamps, either orchestration logs or synthetic transactions. A synthetic client writes sequenced records throughout the drill. RPO is computed from which acknowledged writes survived. RTO is the time from fault injection to sustained functional success.
5. **Repeatable and comparable.** Everything is code. The same scenario run twice produces comparable results, and trends across drills are tracked.
6. **One-command teardown** (kill switch), with an attestation that the twin's data was destroyed.

## What to build

### 1. Discovery & dependency mapping
- Ingest the application and dependency map from {{CMDB / ServiceNow Service Mapping / Dynatrace / vCenter tags / cloud resource graph}}.
- Produce a recovery-order graph per app: identity → DNS/DHCP → PKI/secrets → databases → middleware → app tier → edge.
- Output: `apps/<app>/service-map.yaml`, plus a list of dependencies the map can't resolve. Those are drill risks.

### 2. Twin provisioning (per platform module)
- Isolated network segment (bubble) duplicating production IP space and DNS names, with deny-all egress. Optional jump host or proxy for operator access only.
- Identity first: restore an AD DC from backup into the bubble, seize FSMO roles and handle the RID pool and USN rollback concerns. Never connect it to the production forest.
- Restore or test-failover the workloads using the customer's tooling API: {{Zerto test failover / Veeam SureBackup virtual lab / ASR test failover / AWS DRS drill / SRM test recovery / Rubrik Live Mount}}.
- Data handling: decide per app whether to mask data. Encrypt everything at rest. Track data lineage for the teardown attestation.
- Fidelity / drift report: compare the twin with production on OS and app versions, config hashes, data currency (timestamp of the newest record) and capacity ratio. Fail the run if drift exceeds a threshold.

### 3. Scenario library (declarative, versioned)
Each scenario is a YAML file containing: fault-injection steps, runbook steps (automated or human, each with an expected duration), validation checks, RTO/RPO targets and stop conditions. Minimum set:

| Category | Scenarios |
|---|---|
| HA | Node/host loss, DB primary failover, cluster member loss, storage path loss |
| Site/region | Full primary site loss, AZ/region loss, network partition / split-brain |
| Data | Logical corruption, accidental mass deletion, point-in-time restore |
| Cyber | Ransomware: contain, identify the clean restore point from immutable copies, rebuild identity, restore, validate |
| Foundational | AD/IdP loss, DNS loss, certificate expiry / PKI loss, secrets vault loss |
| External | SaaS / third-party API outage, WAN or carrier loss |

Fault injection uses {{Gremlin / AWS FIS / Azure Chaos Studio / LitmusChaos / vSphere API / scripts}}. Human steps are timed with a simple operator console, so the declaration and decision time is measured, not assumed.

### 4. Measurement harness
- Synthetic transaction clients per app: sequenced writes plus functional reads, run before, during and after the fault.
- Timestamps captured: fault injected, first customer impact, detection (alert fired), declaration, start/end of each runbook step, infrastructure available, application functionally validated, business sign-off.
- Metrics: time to detect, time to declare, infrastructure RTO, application RTO, business RTO, measured RPO (time window and count of lost acknowledged transactions), runbook accuracy (% of steps executed as written), dependency surprises and recovery-order defects.

### 5. Evidence pack & reporting
- Per drill: scorecard (target vs actual, pass/fail), client-view timeline, runbook timeline, isolation proof, drift report, deviations, remediation items with owners, teardown attestation.
- Exports: HTML and PDF for executives, JSON for trend analysis, and a mapping to the relevant control IDs ({{compliance framework}}).
- Trend dashboard across drills, per app and per scenario.

### 6. Governance artifacts
- Rules of engagement / test charter template: scope, stop conditions, contacts, comms plan, approvals.
- RACI for the drill.
- Pre-flight checklist and go/no-go gate.

## Constraints

- No changes to production systems. No agents installed in production unless approved separately.
- Secrets come from {{vault}}. Nothing in code or logs.
- Every module must run unattended from CI and also step-by-step for a facilitated customer workshop.
- Prefer the customer's existing tooling over new licenses. List any new spend explicitly.

## Delivery plan

1. **Ask me** the open questions you need answered, at most 10, before you write code.
2. Propose the architecture (diagram plus a one-page ADR) for the pilot platform. Wait for approval.
3. Build in this order, each step demoable: isolation proof → twin provisioning for one app → synthetic client and measurement → two scenarios (DB failover, site loss) → evidence pack → cyber scenario → drift report → trend dashboard.
4. After each step: show it running, the test results and what's next.

## Acceptance criteria (pilot)

- [ ] The twin for pilot app 1 builds from code, from real backups/replicas, in under {{N}} hours, with no manual steps beyond approved human gates.
- [ ] The isolation proof runs automatically and blocks fault injection when it fails.
- [ ] At least four scenarios are executed (HA, site loss, cyber, foundational), each producing measured RTO/RPO with no hand-entered numbers.
- [ ] The evidence pack is generated automatically and reviewed by {{risk/compliance owner}}.
- [ ] One-command teardown plus a data-destruction attestation.
- [ ] Re-running a scenario gives results within ±10% (repeatability).
- [ ] A runbook gap list with owners is produced from the first drill.
