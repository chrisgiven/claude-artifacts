# Changelog

## [1.3.0] - 2026-08-07

### Security
- **No LAN address remains in the tracked tree.** The four Lab cards that still hardcoded the NAS IP — Sonos Lyrics, Groundwork, AgentOS and Lights — moved to the `data-svc-link` pattern Vaultwarden and Tripwire already used, with their URLs added under `links` in the NAS-only `services.json`. Off-network those cards stay unclickable, which is the intent
- `sync-artifacts.sh` no longer embeds the deploy target; it reads `~/.config/claude-artifacts/nas-host` (overridable with `NAS_HOST`), which also keeps the SSH username out of the repo. A missing file degrades to the existing "NAS cron will catch up" warning
- `Artifacts/todo-dashboard` Quick Links now points at `/` instead of the NAS IP — it is served from that same host anyway

### Notes
- These addresses are still in this repo's public git history; the working-tree fix does not remove them from past commits
- `localhost` cards were left as-is: they expose nothing about the network and those services really do run on the Mac

## [1.2.0] - 2026-07-27

### Added
- Live service health board on the hub — new **Status** section and nav item listing all 10 self-hosted services with up/down, probed from the browser every 30s and on tab focus. Reuses the existing `board`/`led` components and design tokens
- `services.json` support: the service list loads at runtime instead of being hardcoded

### Security
- **The network topology is deliberately not in this repo, which is public.** `index.html` contains the dashboard machinery and zero addresses; the host/port map lives in `services.json`, served only from the NAS and gitignored. Off-network the fetch 404s and the section plus its nav item stay hidden. Verified `raw.githubusercontent.com/.../services.json` returns 404
- Probes use `credentials:'omit'` — CouchDB and ObsidianRemote answer `401 WWW-Authenticate: Basic`, and omitting credentials stops the browser starting an auth negotiation

### Notes
- Pre-existing and unchanged: Lab cards still link to the NAS LAN address on ports 5001/3001/5599, so that address was already public before this release (addressed in 1.3.0)
- nginx serves `index.html` without cache headers; hard-refresh once after a deploy

## [1.1.1] - 2026-07-14

### Added
- Switchboard card (LAB / SWBD) on the hub homepage — local multi-AI project hub (Flask, port 5757); links to localhost like the BCDR card since it runs on the Mac

## [1.1.0] - 2026-07-13

### Added
- `Artifacts/gigplot` — GigPlot, single-file stage plot + input list (tech rider) builder: drag-and-drop stage canvas, multi-plot library, JSON share, PNG export, printable rider
- GigPlot card (LAB / GIG) on the hub homepage
- `gigplot` added to the sync-artifacts.sh allowlist

### Changed
- Hub status board now compares the NAS clone's own git ref against GitHub — the hardcoded `DEPLOYED` SHA (and the bump-on-every-push chore) is gone

### Fixed
- Flushed ~4 weeks of dashboard outputs that were stuck locally because the daily launchd sync was failing (macOS TCC denies rsync in the launchd context; separate fix in progress)

## [1.0.0] - 2026-05-25

### Added
- Initial publish of Claude-generated artifacts and scheduled outputs
- `Artifacts/ai-daily-brief` — AI daily brief dashboard
- `Artifacts/attention-today` — attention/focus dashboard
- `Artifacts/bcdr-ransomware-monitor` — BCDR ransomware monitoring dashboard
- `Artifacts/todo-dashboard` — todo dashboard
- `Scheduled/ai-daily-brief-refresh` — daily brief refresh agent skill
- `Scheduled/bcdr-ransomware-monitor-daily-refresh` — BCDR monitor refresh skill
- `Scheduled/daily-comms-review` — daily communications review skill
- `Scheduled/refresh-dashboard-weather` — weather dashboard refresh skill
