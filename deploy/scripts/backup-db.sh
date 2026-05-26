#!/usr/bin/env bash
# Daily PostgreSQL backup for my-agent (run via cron on VDS).
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups/my-agent}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ENV_FILE="${ENV_FILE:-/opt/projects/my-agent/.env}"

mkdir -p "$BACKUP_DIR"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

DB_URL="${DATABASE_URL:-postgresql://agent:agentpass@127.0.0.1:5437/agent_db}"
OUT="$BACKUP_DIR/agent_db_${TIMESTAMP}.sql.gz"

echo "[backup] Dumping to $OUT"
pg_dump "$DB_URL" | gzip > "$OUT"
find "$BACKUP_DIR" -name 'agent_db_*.sql.gz' -mtime +"$RETAIN_DAYS" -delete
echo "[backup] Done. Kept backups for ${RETAIN_DAYS} days."
