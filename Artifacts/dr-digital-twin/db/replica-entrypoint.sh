#!/bin/sh
# DR-site standby: clone the primary on first start, then stream WAL.
set -e
export PGPASSWORD="$POSTGRES_PASSWORD"
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  until pg_isready -h "$PRIMARY_HOST" -U postgres -q && \
        psql -h "$PRIMARY_HOST" -U postgres -d orders -tAc "SELECT 1 FROM orders LIMIT 1" >/dev/null 2>&1; do
    sleep 1
  done
  pg_basebackup -h "$PRIMARY_HOST" -U postgres -D "$PGDATA" -R -X stream -C -S dr_site_b
  chmod 700 "$PGDATA"
fi
exec postgres -c hot_standby=on
