#!/bin/bash
# Create a Clerk test user, sign it in and make it an Admin (default) or plain User.
# The session lives in this worktree, so agents in other worktrees don't share it.
set -euo pipefail
ROLE="${1:-admin}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PW="${TMPDIR:-/tmp}/zeph-run-playwright"
SESSION="$REPO/.run-dashboard/session"
cd "$REPO"
set -a; . ./.env; set +a
WEB_URL="http://localhost:${WEB_PORT:-3000}"

if [ ! -d "$PW/node_modules/playwright" ]; then
  mkdir -p "$PW"
  (cd "$PW" && npm init -y >/dev/null && npm i playwright@1.57.0 >/dev/null && npx playwright install chromium >/dev/null)
fi
rm -rf "$SESSION"; mkdir -p "$SESSION"

EMAIL="run-check-$(date +%s)-$RANDOM+clerk_test@example.com"
USER_ID=$(curl -s -X POST https://api.clerk.com/v1/users \
  -H "Authorization: Bearer $CLERK_SECRET_KEY" -H 'Content-Type: application/json' \
  -d "{\"email_address\":[\"$EMAIL\"],\"skip_password_requirement\":true}" |
  python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "$USER_ID" > "$SESSION/clerk_user_id"
echo "$EMAIL" > "$SESSION/email"

cp "$HERE/sign-in.mjs" "$PW/"
(cd "$PW" && node sign-in.mjs "$USER_ID" "$SESSION/profile" "$WEB_URL")

psql_run() { docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1"; }
for _ in $(seq 1 20); do
  [ "$(psql_run "select count(*) from users where email='$EMAIL'")" = "1" ] && break
  sleep 1
done
psql_run "update users set role='$ROLE', name='Run check', onboarding_completed_at=now(), ai_notice_acknowledged_at=now() where email='$EMAIL'"
echo "Signed in as $EMAIL ($ROLE) on $WEB_URL. Profile: $SESSION/profile"
