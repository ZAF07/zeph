#!/bin/bash
# Delete the session's Clerk test user, its users row and the saved profile.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
SESSION="${TMPDIR:-/tmp}/zeph-run-playwright/session"
cd "$REPO"
set -a; . ./.env; set +a

curl -s -X DELETE "https://api.clerk.com/v1/users/$(cat "$SESSION/clerk_user_id")" \
  -H "Authorization: Bearer $CLERK_SECRET_KEY"; echo
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "delete from users where email='$(cat "$SESSION/email")'"
rm -rf "$SESSION"
