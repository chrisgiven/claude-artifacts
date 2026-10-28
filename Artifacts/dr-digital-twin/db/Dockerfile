# Postgres with the twin's init, replica and backup scripts baked in, so the
# twin needs no bind mounts (it can then be driven from inside a container).
FROM postgres:16-alpine
COPY primary-init.sh /docker-entrypoint-initdb.d/10-init.sh
COPY replica-entrypoint.sh backup-loop.sh /usr/local/bin/
