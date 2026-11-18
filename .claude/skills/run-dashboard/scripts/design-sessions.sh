#!/bin/bash
# Make the two signed-in sessions the design pixel test needs (web/design/compare.cjs):
# a plain User, and an Admin carrying the zeph-design-as=admin cookie.
# Reuses start-session.sh, so the stack must be running (make up) with real
# data, not design fixtures. Saves Playwright storageState files outside the
# repo and prints the STATE_USER / STATE_ADMIN lines to export.
# Remove the test users afterwards with design-sessions-cleanup.sh.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PW="${TMPDIR:-/tmp}/zeph-run-playwright"
SESSION="$REPO/.run-dashboard/session"
OUT="${TMPDIR:-/tmp}/zeph-design-sessions/$(basename "$REPO")"
rm -rf "$OUT"; mkdir -p "$OUT"

for ROLE in user admin; do
  "$HERE/start-session.sh" "$ROLE"
  cp "$SESSION/clerk_user_id" "$OUT/$ROLE.clerk_user_id"
  cp "$SESSION/email" "$OUT/$ROLE.email"
  cp "$HERE/save-state.mjs" "$PW/"
  (cd "$PW" && node save-state.mjs "$SESSION/profile" "$OUT/$ROLE.json" "$ROLE")
  rm -rf "$SESSION"
done

echo "export STATE_USER=$OUT/user.json"
echo "export STATE_ADMIN=$OUT/admin.json"
