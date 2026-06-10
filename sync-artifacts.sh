#!/bin/bash
# Syncs Claude scheduled-task outputs from ~/Documents/Claude into this repo,
# pushes to GitHub, and pulls on the NAS so the portfolio stays current.
# Runs daily via launchd: ~/Library/LaunchAgents/com.chrisgiven.claude-artifacts-sync.plist
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin:$PATH

REPO="$HOME/Projects/claude-artifacts"
SRC="$HOME/Documents/Claude"
NAS="givster@192.168.1.94"
NAS_REPO="/volume1/Web/projects/claude-artifacts"

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

ssh -o BatchMode=yes -o ConnectTimeout=10 "$NAS" "cd $NAS_REPO && git pull"
echo "$(date '+%F %T') synced and deployed"
