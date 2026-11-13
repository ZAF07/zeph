#!/bin/bash
# Open a Dashboard path as the signed-in session user and screenshot it.
# Usage: drive.sh <path> <screenshot.png> [viewport width]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PW="${TMPDIR:-/tmp}/zeph-run-playwright"
SHOT="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
set -a; . "$REPO/.env"; set +a
cp "$HERE/drive.mjs" "$PW/"
cd "$PW" && node drive.mjs "$1" "$SHOT" "${3:-1280}" "$REPO/.run-dashboard/session/profile" \
  "http://localhost:${WEB_PORT:-3000}"
