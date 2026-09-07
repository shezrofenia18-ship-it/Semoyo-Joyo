#!/usr/bin/env bash
# Self-healing PostgreSQL bootstrap for the DEV container only.
# - Re-installs PostgreSQL 15 if binaries were lost (pod restart)
# - Initializes /app/pgdata if empty
# - Starts the server if not running
# - Ensures database + role exist
# In production (Coolify) this script is NOT used; DATABASE_URL points to the postgres service.

set -u
PG_BIN=/usr/lib/postgresql/15/bin
PG_DATA=/app/pgdata
PG_LOG=/app/pglog
DB_NAME="${PG_DB_NAME:-mbg_erp}"
DB_USER="${PG_DB_USER:-mbg_user}"
DB_PASS="${PG_DB_PASS:-mbg_pass_2024}"

log() { echo "[ensure_postgres] $*"; }

if [ ! -x "$PG_BIN/pg_ctl" ]; then
  log "PostgreSQL binaries missing -> installing (apt)..."
  apt-get update -qq >/dev/null 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql postgresql-contrib >/dev/null 2>&1
  # Debian auto-starts a cluster on 5432 via pg_ctlcluster; stop it so ours can use the port
  pg_ctlcluster 15 main stop >/dev/null 2>&1 || true
fi

if ! id postgres >/dev/null 2>&1; then
  log "creating postgres system user"
  useradd -r -s /bin/bash postgres
fi

mkdir -p "$PG_DATA" "$PG_LOG"
chown -R postgres:postgres "$PG_DATA" "$PG_LOG"
chmod 700 "$PG_DATA"

if [ ! -f "$PG_DATA/PG_VERSION" ]; then
  log "initializing data directory $PG_DATA"
  su postgres -c "$PG_BIN/initdb -D $PG_DATA -U postgres --auth=trust -E UTF8" >/dev/null 2>&1
fi

# Remove stale pid file if server is not actually running
if [ -f "$PG_DATA/postmaster.pid" ]; then
  PID=$(head -1 "$PG_DATA/postmaster.pid")
  if ! kill -0 "$PID" 2>/dev/null; then
    log "removing stale postmaster.pid"
    rm -f "$PG_DATA/postmaster.pid"
  fi
fi

if ! su postgres -c "$PG_BIN/pg_isready -h localhost -p 5432" >/dev/null 2>&1; then
  log "starting PostgreSQL"
  su postgres -c "$PG_BIN/pg_ctl -D $PG_DATA -l $PG_LOG/postgres.log -o '-p 5432 -c listen_addresses=localhost' start" >/dev/null 2>&1
  for i in $(seq 1 20); do
    if su postgres -c "$PG_BIN/pg_isready -h localhost -p 5432" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
fi

if su postgres -c "$PG_BIN/pg_isready -h localhost -p 5432" >/dev/null 2>&1; then
  # Ensure role + database exist (idempotent)
  su postgres -c "$PG_BIN/psql -h localhost -p 5432 -tAc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\"" | grep -q 1 || \
    su postgres -c "$PG_BIN/psql -h localhost -p 5432 -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" >/dev/null
  su postgres -c "$PG_BIN/psql -h localhost -p 5432 -tAc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\"" | grep -q 1 || \
    su postgres -c "$PG_BIN/psql -h localhost -p 5432 -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" >/dev/null
  log "PostgreSQL ready (db=$DB_NAME user=$DB_USER)"
  exit 0
else
  log "ERROR: PostgreSQL failed to start. See $PG_LOG/postgres.log"
  exit 1
fi
