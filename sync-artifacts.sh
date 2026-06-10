#!/bin/bash
# Syncs Claude scheduled-task outputs from ~/Documents/Claude into this repo
# and pushes to GitHub. The NAS pulls on its own half-hourly cron (givster's
# crontab on 192.168.1.94), so no Mac->NAS SSH is needed here.
# Runs daily via launchd: ~/Library/LaunchAgents/com.chrisgiven.claude-artifacts-sync.plist
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin:$PATH

REPO="$HOME/Projects/claude-artifacts"
SRC="$HOME/Documents/Claude"
cd "$REPO"

# Only sync paths already published; CLAUDE.md files hold private memory
for d in ai-daily-brief bcdr-ransomware-monitor; do
  rsync -a --exclude .DS_Store --exclude CLAUDE.md "$SRC/Artifacts/$d/" "Artifacts/$d/"
done
for d in ai-daily-brief-refresh bcdr-ransomware-monitor-daily-refresh daily-comms-review refresh-dashboard-weather; do
  rsync -a --exclude .DS_Store --exclude CLAUDE.md "$SRC/Scheduled/$d/" "Scheduled/$d/"
done

if [[ -z "$(git status --porcelain)" ]]; then
  echo "$(date '+%F %T') no changes"
  exit 0
fi

git add -A
git commit -m "chore: auto-sync artifact outputs $(date '+%F')"
git push

echo "$(date '+%F %T') synced and pushed (NAS pulls via its own cron)"
