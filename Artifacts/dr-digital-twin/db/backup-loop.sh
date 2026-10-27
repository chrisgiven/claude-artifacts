#!/bin/sh
# Scheduled logical backups to the vault (stand-in for an immutable backup target).
# A dump that captures a corrupted database is still written: picking the clean
# restore point is part of the recovery runbook, as it is in a real cyber event.
set -e
export PGPASSWORD="$POSTGRES_PASSWORD"
while true; do
  ts=$(date +%s)
  if pg_dump -Fc -d "$DB_DSN" -f "/vault/.tmp-$ts" 2>/dev/null; then
    mv "/vault/.tmp-$ts" "/vault/orders-$ts.dump"
  else
    rm -f "/vault/.tmp-$ts"
  fi
  ls -1t /vault/orders-*.dump 2>/dev/null | tail -n +21 | xargs -r rm -f
  sleep "$BACKUP_INTERVAL"
done
