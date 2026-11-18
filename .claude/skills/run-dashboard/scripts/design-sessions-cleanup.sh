#!/bin/bash
# Delete the Clerk test users, their users rows and the storageState files
# made by design-sessions.sh for this worktree.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
OUT="${TMPDIR:-/tmp}/zeph-design-sessions/$(basename "$REPO")"
cd "$REPO"
set -a; . ./.env; set +a

for ROLE in user admin; do
  [ -f "$OUT/$ROLE.clerk_user_id" ] || continue
  curl -s -X DELETE "https://api.clerk.com/v1/users/$(cat "$OUT/$ROLE.clerk_user_id")" \
    -H "Authorization: Bearer $CLERK_SECRET_KEY"; echo
  docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -c "delete from users where email='$(cat "$OUT/$ROLE.email")'"
done
rm -rf "$OUT"
