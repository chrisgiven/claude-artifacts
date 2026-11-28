# Vaultwarden restore drill (proposed scenario, increment 0.2.2)

Status: specified 2026-11-27, not built. Needs a Docker host to build and run (Mac or NAS), not the Claude VM.

## Why

The home-lab assessment (BCDR Assessment Toolkit, "Home Lab (Big Poppy reference)") scores Vaultwarden
B3 "restore tested" and P3 "DR exercise" as not yet evidenced, and its current RTO as unknown.
Vaultwarden is Tier 1 with a proposed RTO of 4 h and RPO of 24 h. This drill produces a measured RTO
and an evidence pack for both controls, using synthetic data only.

## Rules

- Synthetic vault only. Never mount, copy or restore the real `/volume1/docker/vaultwarden` data or
  its backups into the twin. The drill proves the procedure and the backup format, not the live backup.
- Same isolation and teardown gates as every other scenario: fault only after the isolation proof passes.
- Pin the image to the version running in production (read it from Portainer, don't use `latest`).

## Topology addition (docker-compose.yml)

| Service | Site | Role | Notes |
|---|---|---|---|
| `vw-a` | A | vaultwarden primary | `vaultwarden/server:<prod version>`, SQLite at `/data`, `SIGNUPS_ALLOWED=false` after seeding, bubble network only |
| `vw-backup` | shared | backup | Loop every `BACKUP_INTERVAL`: `sqlite3 /data/db.sqlite3 ".backup /vault/vw-<ts>.sqlite3"` plus `tar` of `/data/attachments` and `rsa_key*`, keep 20 |

`twin.yaml` gains `vw-a` and `vw-backup` under `expected.services`, and a `backup` entry for the vault
so the drift check fails if no Vaultwarden backup is newer than `max_age_s`.

## Load and measurement

- Seed: create one synthetic user through the API (fixed test email and master password from the twin's env, never a real one), then write N synthetic items.
- Load: a writer in the existing `load.py` pattern that adds a synthetic item every second via the API and records acknowledged item IDs.
- RTO = fault → first of 5 consecutive successful item reads/writes through `vw-a`.
- RPO = acknowledged synthetic items missing after recovery (`measure.py` already computes this shape).

## Scenario (scenarios/vaultwarden-restore.yaml)

```yaml
id: vaultwarden-restore
title: "Vaultwarden: database loss, restore from backup"
tier: Tier 1
description: >
  The Vaultwarden SQLite database is deleted on the primary. Recovery restores the
  last clean backup and validates that the vault answers and items are readable.
targets: {rto_s: 14400, rpo_s: 86400}   # proposed Tier 1 targets: 4 h / 24 h
warmup_s: 45
fault:
  - {name: "Fault: Vaultwarden database deleted", action: exec, service: vw-a, command: "rm -f /data/db.sqlite3 /data/db.sqlite3-wal /data/db.sqlite3-shm"}
runbook:
  - {name: "Declare incident", actor: human, action: declare}
  - {name: "Stop Vaultwarden", actor: runbook, action: stop, services: [vw-a]}
  - {name: "Identify last clean backup", actor: runbook, action: find_clean_file_backup, prefix: "vw-"}
  - {name: "Restore database and attachments", actor: runbook, action: restore_file_backup, service: vw-a, target: /data/db.sqlite3}
  - {name: "Start Vaultwarden", actor: runbook, action: start, services: [vw-a]}
  - {name: "Validate vault via API", actor: runbook, action: wait_healthy, timeout_s: 300}
```

## Provider work (drtwin/providers/docker.py)

| New action | Does |
|---|---|
| `exec` | `docker compose exec -T <service> sh -c <command>` |
| `find_clean_file_backup` | Like `_find_clean_backup`, over `/vault/<prefix><ts>.sqlite3` |
| `restore_file_backup` | Copy the chosen backup into `<service>:<target>` (`docker compose cp`), restore attachments tarball |

`wait_healthy` needs a per-scenario health check: `GET /alive` on `vw-a` plus one synthetic item read,
instead of the orders LB.

## Tests

- `tests/test_scenario_drift.py`: the new YAML validates against the provider's action list.
- A unit test for `find_clean_file_backup` picking the newest backup older than `t0`.

## Done when

A run writes `reports/<ts>/` with a measured RTO/RPO for `vaultwarden-restore`, isolation proof and
teardown attestation passed. Then score Vaultwarden B3 and P3 in the toolkit and enter the measured RTO.
