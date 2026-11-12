#!/bin/bash
# Create a Clerk test user, sign it in and make it an Admin (default) or plain User.
set -euo pipefail
ROLE="${1:-admin}"
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PW="${TMPDIR:-/tmp}/zeph-run-playwright"
SESSION="$PW/session"
cd "$REPO"
set -a; . ./.env; set +a

if [ ! -d "$PW/node_modules/playwright" ]; then
  mkdir -p "$PW"
  (cd "$PW" && npm init -y >/dev/null && npm i playwright@1.57.0 >/dev/null && npx playwright install chromium >/dev/null)
fi
rm -rf "$SESSION"; mkdir -p "$SESSION"

EMAIL="run-check-$(date +%s)+clerk_test@example.com"
USER_ID=$(curl -s -X POST https://api.clerk.com/v1/users \
  -H "Authorization: Bearer $CLERK_SECRET_KEY" -H 'Content-Type: application/json' \
  -d "{\"email_address\":[\"$EMAIL\"],\"skip_password_requirement\":true}" |
  python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "$USER_ID" > "$SESSION/clerk_user_id"
echo "$EMAIL" > "$SESSION/email"

cp "$HERE/sign-in.mjs" "$PW/"
(cd "$PW" && node sign-in.mjs "$USER_ID" "$SESSION/profile")

psql_run() { docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1"; }
for _ in $(seq 1 20); do
  [ "$(psql_run "select count(*) from users where email='$EMAIL'")" = "1" ] && break
  sleep 1
done
psql_run "update users set role='$ROLE', name='Run check', onboarding_completed_at=now(), ai_notice_acknowledged_at=now() where email='$EMAIL'"
echo "Signed in as $EMAIL ($ROLE). Profile: $SESSION/profile"
