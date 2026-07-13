# Changelog

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
