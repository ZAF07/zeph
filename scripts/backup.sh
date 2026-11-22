#!/usr/bin/env bash
# Nightly Postgres backup, copied off the server to Cloudflare R2 (issue 16).
# Runs from deploy's crontab; see docs/DEPLOYMENT_GUIDE.md. Local copies are
# kept 7 days; the R2 bucket deletes its copies after 30 days.
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
backup_dir="${BACKUP_DIR:-$HOME/backups}"
remote="${BACKUP_REMOTE:-r2:zeph-backups}"
dump_file="$backup_dir/zeph-$(date -u +%Y-%m-%dT%H%M%SZ).dump"
partial_file="$dump_file.partial"

trap 'rm -f "$partial_file"' EXIT
mkdir -p "$backup_dir"
cd "$project_dir"

docker compose exec -T postgres \
  sh -c 'pg_dump --format=custom -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "$partial_file"
mv "$partial_file" "$dump_file"

rclone copy "$dump_file" "$remote"
find "$backup_dir" -name 'zeph-*.dump' -mtime +7 -delete

echo "$(date -u +%FT%TZ) backed up $(basename "$dump_file")"
