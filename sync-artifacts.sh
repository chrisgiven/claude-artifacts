#!/bin/bash
# Syncs Claude scheduled-task outputs from ~/Claude into this repo and pushes
# to GitHub, then updates the NAS clone over SSH. ~/Claude is the real home of
# Artifacts/ and Scheduled/ (moved out of ~/Documents 2026-07-13 so this job
# doesn't need a TCC/Full Disk Access grant under launchd; symlinks remain at
# ~/Documents/Claude/Artifacts and ~/Documents/Claude/Scheduled).
# Runs daily via launchd: ~/Library/LaunchAgents/com.chrisgiven.claude-artifacts-sync.plist
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin:$PATH

REPO="$HOME/Projects/claude-artifacts"
SRC="$HOME/Claude"
cd "$REPO"

# Only sync paths already published; CLAUDE.md files hold private memory
for d in ai-daily-brief bcdr-ransomware-monitor gigplot; do
  rsync -a --exclude .DS_Store --exclude CLAUDE.md "$SRC/Artifacts/$d/" "Artifacts/$d/"
done
for d in ai-daily-brief-refresh bcdr-ransomware-monitor-daily-refresh daily-comms-review refresh-dashboard-weather; do
  rsync -a --exclude .DS_Store --exclude CLAUDE.md "$SRC/Scheduled/$d/" "Scheduled/$d/"
done

if [[ -z "$(git status --porcelain)" ]]; then
  echo "$(date '+%F %T') no changes"
else
  git add -A
  git commit -m "chore: auto-sync artifact outputs $(date '+%F')"
  git push
  echo "$(date '+%F %T') synced and pushed"
fi

# Bring the NAS clone current immediately; its own cron is just a fallback.
# Non-fatal: if the NAS is unreachable it catches up on its next cron run.
if ssh -o BatchMode=yes -o ConnectTimeout=10 givster@192.168.1.94 \
    'cd /volume1/Web/projects/claude-artifacts && git fetch origin && git reset --hard origin/main' >/dev/null 2>&1; then
  echo "$(date '+%F %T') NAS clone updated"
else
  echo "$(date '+%F %T') WARNING: NAS clone not updated (unreachable?); NAS cron will catch up"
fi
