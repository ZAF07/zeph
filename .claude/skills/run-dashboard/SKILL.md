---
name: run-dashboard
description: Launch the Docker stack and drive the Dashboard in a real browser as a signed-in Admin (or plain User) with Playwright. Use for /run checks of any Dashboard or admin page.
---

# Run the Dashboard

Verified 2026-11-12 on macOS with Docker Desktop. All secrets come from `.env`.

## 1. Start (or rebuild) the stack

```bash
make restart
```

Always rebuild after code changes: the running containers keep the old code
until then. Web is on http://localhost:3000, backend on http://localhost:8000.
For a few seconds after a restart the backend may answer 401 to valid tokens;
wait and reload.

## 2. Start a signed-in session

```bash
.claude/skills/run-dashboard/scripts/start-session.sh          # Admin
.claude/skills/run-dashboard/scripts/start-session.sh user     # plain User
```

It installs Playwright once (in `$TMPDIR/zeph-run-playwright`), creates a Clerk
test user (`run-check-<time>+clerk_test@example.com`), signs it in with a Clerk
sign-in ticket, waits for its row in `users`, marks onboarding done and (for
Admin) sets `role = 'admin'`. It saves the browser profile and the user id in
`$TMPDIR/zeph-run-playwright/session/`.

## 3. Drive pages

```bash
.claude/skills/run-dashboard/scripts/drive.sh /admin/knowledge shot.png
.claude/skills/run-dashboard/scripts/drive.sh /admin/persona shot.png 390
```

Opens the path as the signed-in user, waits for the page to settle, saves a
screenshot (optional third argument is the viewport width) and prints page
errors. **Look at the screenshot.** For clicks and typing, copy `drive.mjs`
into the scratchpad and add the steps; run it with
`node <script>` from `$TMPDIR/zeph-run-playwright` so it finds Playwright.

Tips:
- Accept `confirm()` dialogs with `page.on("dialog", (d) => d.accept())`.
- The Knowledge text editor is CodeMirror: target `.cm-content`. CodeMirror
  only draws the lines on screen, so compare text by content, not length.
- Use plain screenshots, not `fullPage`, to check layout at 390px:
  full-page capture resizes the window and can misalign CodeMirror's gutter.
- "Failed to load resource / ERR_NETWORK_CHANGED" for Clerk's own scripts
  comes from navigating away and is not a page error.
- Read or shift database state with
  `docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB`
  (after `set -a; . ./.env; set +a`). Shift timestamps instead of waiting.

## 4. Clean up

```bash
.claude/skills/run-dashboard/scripts/cleanup.sh
```

Deletes the Clerk user, its `users` row and the saved profile. Also undo any
data the run changed (e.g. edited Knowledge documents).
