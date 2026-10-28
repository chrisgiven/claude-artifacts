#!/bin/sh
# Runs once on first start of the primary: schema + replication access.
set -e
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<SQL
CREATE TABLE orders (
  id          bigserial PRIMARY KEY,
  client_seq  bigint UNIQUE NOT NULL,
  site        text,
  node        text,
  created_at  timestamptz DEFAULT now()
);
INSERT INTO orders (client_seq, site, node) VALUES (0, 'seed', 'seed');
SQL
echo "host replication all all scram-sha-256" >> "$PGDATA/pg_hba.conf"
