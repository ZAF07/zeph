---
name: run-dashboard
description: Launch the Docker stack and drive the Dashboard in a real browser as a signed-in Admin (or plain User) with Playwright. Use for /run checks of any Dashboard or admin page.
---

# Run the Dashboard

Verified 2026-11-13 on macOS with Docker Desktop. All secrets come from `.env`.

Works the same in the main folder and in any git worktree. In a worktree, run
`make worktree-setup` once first: it gives the worktree its own ports,
database and `.env`. The scripts read the web port and Compose project from
the worktree's `.env` and keep the browser session in `.run-dashboard/`
inside the worktree, so agents in different worktrees never share a session
or test user.

## 1. Start (or rebuild) the stack

```bash
make restart
```

Always rebuild after code changes: the running containers keep the old code
until then. Web is on `http://localhost:$WEB_PORT`, backend on
`http://localhost:$BACKEND_PORT` (3000 and 8000 in the main folder; see the
worktree's `.env` otherwise).
For a few seconds after a restart the backend may answer 401 to valid tokens;
wait and reload.

## 2. Start a signed-in session

```bash
.claude/skills/run-dashboard/scripts/start-session.sh          # Admin
.claude/skills/run-dashboard/scripts/start-session.sh user     # plain User
```

It installs Playwright once (shared, in `$TMPDIR/zeph-run-playwright`), creates a Clerk
test user (`run-check-<time>-<random>+clerk_test@example.com`), signs it in with a Clerk
sign-in ticket, waits for its row in `users`, marks onboarding done and (for
Admin) sets `role = 'admin'`. It saves the browser profile and the user id in
`.run-dashboard/session/` in this worktree (git-ignored).

## 3. Drive pages

```bash
.claude/skills/run-dashboard/scripts/drive.sh /admin/knowledge shot.png
.claude/skills/run-dashboard/scripts/drive.sh /admin/persona shot.png 390
```

Opens the path as the signed-in user, waits for the page to settle, saves a
screenshot (optional third argument is the viewport width) and prints page
errors. **Look at the screenshot.** For clicks and typing, copy `drive.mjs`
into the scratchpad and add the steps; run it with
`node <script> <path> <shot> <width> <repo>/.run-dashboard/session/profile http://localhost:$WEB_PORT`
from `$TMPDIR/zeph-run-playwright` so it finds Playwright.

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
- Telegram: only the main stack registers the bot's webhook and runs ngrok.
  In a worktree, post an update straight to the worktree's backend:
  `curl -X POST http://localhost:$BACKEND_PORT/telegram/webhook -H "X-Telegram-Bot-Api-Secret-Token: $TELEGRAM_WEBHOOK_SECRET" -H 'Content-Type: application/json' -d '<update json>'`.
  The bot's replies still go to the real chat.
- `make db-copy` (in a worktree) replaces its database with a copy of the
  main stack's, e.g. to check a migration on real data. Both stacks must run.
  It removes Telegram links from the copy so the worktree's Check-ins never
  reach real Users.

## 4. Clean up

```bash
.claude/skills/run-dashboard/scripts/cleanup.sh
```

Deletes the Clerk user, its `users` row and the saved profile. Also undo any
data the run changed (e.g. edited Knowledge documents).

In a worktree, when your work is done, also run `make worktree-teardown`. It
stops the worktree's stack and deletes its containers, images, network and
database, so stacks don't pile up on the machine. It refuses to run in the
main folder.
