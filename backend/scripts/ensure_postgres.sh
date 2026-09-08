#!/usr/bin/env bash
# Self-healing PostgreSQL bootstrap for the DEV container only.
#
# Problem: the container's /usr is reset on pod restart, so apt-installed PostgreSQL
# binaries disappear while /app (data) and /root persist. Strategy:
#   1. Prefer a PORTABLE BUNDLE at /root/pg15 (binaries + share + shared libs).
#   2. Fallback to system binaries (/usr/lib/postgresql/15).
#   3. Last resort: apt-get install, then (re)create the portable bundle.
# Then: ensure postgres OS user, init /app/pgdata if empty, start server, ensure role+db.
# In production (Coolify) this script is NOT used; DATABASE_URL points to the postgres service.

set -u
BUNDLE=/root/pg15
SYS_BIN=/usr/lib/postgresql/15/bin
PG_DATA=/app/pgdata
PG_LOG=/app/pglog
DB_NAME="${PG_DB_NAME:-mbg_erp}"
DB_USER="${PG_DB_USER:-mbg_user}"
DB_PASS="${PG_DB_PASS:-mbg_pass_2024}"

log() { echo "[ensure_postgres] $*"; }

PG_BIN=""
LDPATH=""

use_bundle() {
  if [ -x "$BUNDLE/usr/lib/postgresql/15/bin/postgres" ]; then
    PG_BIN="$BUNDLE/usr/lib/postgresql/15/bin"
    LDPATH="$BUNDLE/libs"
    return 0
  fi
  return 1
}

create_bundle() {
  log "creating portable bundle at $BUNDLE"
  rm -rf "$BUNDLE"
  mkdir -p "$BUNDLE/usr/lib/postgresql/15" "$BUNDLE/usr/share/postgresql" "$BUNDLE/libs"
  cp -a /usr/lib/postgresql/15/bin "$BUNDLE/usr/lib/postgresql/15/"
  cp -a /usr/lib/postgresql/15/lib "$BUNDLE/usr/lib/postgresql/15/"
  cp -a /usr/share/postgresql/15 "$BUNDLE/usr/share/postgresql/"
  for f in "$BUNDLE"/usr/lib/postgresql/15/bin/* "$BUNDLE"/usr/lib/postgresql/15/lib/*.so; do
    ldd "$f" 2>/dev/null | awk '/=> \//{print $3}'
  done | sort -u | while read -r lib; do cp -Ln "$lib" "$BUNDLE/libs/" 2>/dev/null || true; done
  # never ship core libc pieces; always use the system ones
  (cd "$BUNDLE/libs" && rm -f libc.so.6 libm.so.6 libpthread.so.0 libdl.so.2 librt.so.1 libresolv.so.2 ld-linux* libgcc_s.so.1 libnsl* libutil.so.1)
  chmod 711 /root
  chmod -R a+rX "$BUNDLE"
}

if ! use_bundle; then
  if [ -x "$SYS_BIN/postgres" ]; then
    log "bundle missing, using system binaries and creating bundle"
    create_bundle
  else
    log "PostgreSQL binaries missing -> installing (apt)..."
    apt-get update -qq >/dev/null 2>&1
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql postgresql-contrib >/dev/null 2>&1
    pg_ctlcluster 15 main stop >/dev/null 2>&1 || true
    if [ -x "$SYS_BIN/postgres" ]; then
      create_bundle
    fi
  fi
  use_bundle || { [ -x "$SYS_BIN/postgres" ] && PG_BIN="$SYS_BIN"; }
fi

if [ -z "$PG_BIN" ]; then
  log "ERROR: no PostgreSQL binaries available"
  exit 1
fi

if ! id postgres >/dev/null 2>&1; then
  log "creating postgres system user"
  useradd -r -s /bin/bash postgres
fi

mkdir -p "$PG_DATA" "$PG_LOG" /var/run/postgresql
chown -R postgres:postgres "$PG_DATA" "$PG_LOG" /var/run/postgresql
chmod 700 "$PG_DATA"
chmod 711 /root 2>/dev/null || true

# helper: run as postgres with correct lib path
pg() { su postgres -c "LD_LIBRARY_PATH=$LDPATH $PG_BIN/$*"; }

if [ ! -f "$PG_DATA/PG_VERSION" ]; then
  log "initializing data directory $PG_DATA"
  pg "initdb -D $PG_DATA -U postgres --auth=trust -E UTF8" >/dev/null 2>&1
fi

# Remove stale pid file if server is not actually running
if [ -f "$PG_DATA/postmaster.pid" ]; then
  PID=$(head -1 "$PG_DATA/postmaster.pid")
  if ! kill -0 "$PID" 2>/dev/null; then
    log "removing stale postmaster.pid"
    rm -f "$PG_DATA/postmaster.pid"
  fi
fi

if ! pg "pg_isready -h localhost -p 5432" >/dev/null 2>&1; then
  log "starting PostgreSQL ($PG_BIN)"
  pg "pg_ctl -D $PG_DATA -l $PG_LOG/postgres.log -o '-p 5432 -c listen_addresses=localhost' start" >/dev/null 2>&1
  for _ in $(seq 1 30); do
    if pg "pg_isready -h localhost -p 5432" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
fi

if pg "pg_isready -h localhost -p 5432" >/dev/null 2>&1; then
  pg "psql -h localhost -p 5432 -tAc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\"" | grep -q 1 || \
    pg "psql -h localhost -p 5432 -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" >/dev/null
  pg "psql -h localhost -p 5432 -tAc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\"" | grep -q 1 || \
    pg "psql -h localhost -p 5432 -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" >/dev/null
  log "PostgreSQL ready (db=$DB_NAME user=$DB_USER bin=$PG_BIN)"
  exit 0
else
  log "ERROR: PostgreSQL failed to start. See $PG_LOG/postgres.log"
  tail -5 "$PG_LOG/postgres.log" 2>/dev/null
  exit 1
fi
