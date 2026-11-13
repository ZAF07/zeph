# 01 — Run a stack per worktree, side by side

Status: completed

## Parent

None. Developer tooling, raised on 2026-11-13 while Photos issue 04 and MVP issue 20 were built in parallel worktrees.

## Problem

Several agents now work at once, each in its own git worktree. Each one needs the running app to verify its work (`/run`), but only one Docker stack can run at a time, so agents block each other. Today:

1. `docker-compose.yml` hard-codes host ports 5432, 8000 and 3000, so a second stack can't start. `.env` pins `NEXT_PUBLIC_API_URL` (`http://localhost:8000`) and `DASHBOARD_URL` (`http://localhost:3000`, also the backend's only CORS origin) to those ports.
2. Every backend registers the bot's Telegram webhook when it starts (`src/companion/prestart.py`). There is one bot and one ngrok domain (the free plan runs one tunnel), so the last stack started takes all real Telegram traffic.
3. The run-dashboard scripts (`.claude/skills/run-dashboard/scripts/`) hard-code `localhost:3000`, call `docker compose` without a project name (so they can't find a worktree's stack), and keep the signed-in browser in one shared `$TMPDIR/zeph-run-playwright/session`. Two agents overwrite each other's session, and one agent's `cleanup.sh` deletes the other's Clerk test user.
4. Starting a worktree under the main project name (the workaround used in Photos issue 04) shares one database, so both schedulers send Check-ins to the same Telegram User twice.

Already safe in parallel: `pytest` (testcontainers on random ports), `vitest`, evals.

## What to build

- **Ports per worktree.** Compose reads `WEB_PORT`, `BACKEND_PORT` and `POSTGRES_PORT`, defaulting to 3000, 8000 and 5432, so the main folder works as today. `NEXT_PUBLIC_API_URL` and `DASHBOARD_URL` are built from them, so CORS and Dashboard links follow.
- **`make worktree-setup`.** Run once in a new worktree: copies `.env` from the main folder, picks a free set of ports (e.g. 3010/8010/5442, then 3020/8020/5452), sets `COMPOSE_PROJECT_NAME` to the folder name (its own database volume), turns off Telegram webhook registration, and installs Python and web packages. It never edits the main folder's `.env`.
- **Only one stack owns Telegram.** A setting (e.g. `TELEGRAM_WEBHOOK_REGISTER`, on by default) lets `prestart.py` skip registering the webhook. ngrok runs only in the main stack. Other stacks test Telegram by posting updates straight to `localhost:<BACKEND_PORT>/telegram/webhook`; the bot's replies still go to the real chat.
- **Run scripts per worktree.** The run-dashboard scripts read the worktree's web port and compose project, and keep the browser session inside the worktree (not a shared `$TMPDIR` folder), so `cleanup.sh` only removes its own test user. Update `SKILL.md` to match.
- **Optional: `make db-copy`.** Copies the main stack's database into the worktree's, for runs that need an existing install (e.g. checking a migration).
- **`make worktree-teardown`** (added 2026-11-13 at the user's request). Stops the worktree's stack and deletes its containers, images, network and database volume; refuses to run in the main folder. `CLAUDE.md`'s "When done" steps tell every agent to run it, so stacks don't pile up.
- Document the setup in `CLAUDE.md` (Git workflow (parallel agents)) so every agent runs `make worktree-setup` first.

## Acceptance criteria

- [x] Two worktrees run their full stacks at the same time on different ports, each with its own database, and the main folder still runs on 3000/8000/5432 with no changes to its `.env`
- [x] Sign-in works on a worktree's Dashboard port (Clerk dev instance), and its Dashboard talks to its own backend (no CORS errors)
- [x] Only the main stack registers the Telegram webhook; a worktree stack answers an update posted to its own webhook
- [x] Two agents can run `start-session.sh`, `drive.sh` and `cleanup.sh` in different worktrees at the same time without touching each other's session or test user
- [x] `make worktree-setup` sets up a fresh worktree in one step and never edits the main folder
- [x] `make worktree-teardown` leaves nothing of the worktree's stack behind (containers, images, network, volume) and refuses to run in the main folder
- [x] `make check` passes
- [x] Verified by running two stacks side by side and driving both Dashboards with the run scripts

## Notes

- Each stack runs Postgres, the backend (with its embedding model) and the Next dev server; three or four at once will use a lot of RAM.
- If two agents ever need to test from a phone at once, a second test bot from BotFather (its own token, webhook and ngrok domain) is the way; out of scope here.
- Shared files this touches: `docker-compose.yml`, `Makefile`, `src/companion/prestart.py` and `config.py`, the run-dashboard skill, `CLAUDE.md`.

## Blocked by

None.

## Comments

Verification, 2026-11-13 (main stack on 3000/8000/5432 kept running throughout):

- **Two stacks side by side.** `make worktree-setup` gave worktree `ai-chat-companion-dev-env-01` 3010/8010/5442 and a second worktree 3020/8020/5452. Both ran their full stacks next to the main one, each with its own `<project>_postgres-data` volume. Main's `.env` md5 was the same before and after. `docker compose config` with main's `.env` and the new compose file still resolves 3000/8000/5432, `DASHBOARD_URL=http://localhost:3000`, `NEXT_PUBLIC_API_URL=http://localhost:8000`, and includes ngrok.
- **Sign-in and CORS.** `start-session.sh` signed in through Clerk on 3010 (Admin) and 3020 (User). `/admin/settings` on 3010 and `/` on 3020 loaded. Every `/api/*` call went to that worktree's own backend (8010 or 8020) and returned 200, with no page or console errors.
- **Telegram.** Both worktree backends logged "Telegram webhook registration is turned off; skipping it". `getWebhookInfo` still pointed at main's ngrok domain. Posting a `/start` update to `localhost:8010/telegram/webhook` gave 401 with a wrong secret and 200 with the right one. The bot replied to the real chat (no send errors), and main's backend saw no request.
- **Run scripts at once.** `start-session.sh`, then `drive.sh`, then `cleanup.sh` ran at the same time in both worktrees. Each one used its own `.run-dashboard/session` and its own Clerk user (`run-check-<time>-<random>`, created in the same second), and each cleanup deleted only its own user. The first attempt timed out while the Next dev servers were still compiling their first page; a retry after warm-up worked.
- **Setup and teardown.** Setup is one step: `.env`, then `uv sync`, then `pnpm install`. Run in the main folder, the script refuses ("Run this in a worktree, not the main folder.", exit 1), and so do `make worktree-teardown` and `make db-copy`. Teardown removed the worktree's containers, network, volume and both built images (it works even when the stack is already stopped). Afterwards only the main stack's containers, volume, network and images were left.
- **`make db-copy`.** The worktree ended up with main's user and 6 Knowledge documents, and with 0 Telegram links (removed on purpose). With the main stack unreachable (`MAIN_DIR=/nonexistent`), it failed before dropping anything, and the worktree's data and backend were untouched. The first version of this target had read from the worktree itself whenever `COMPOSE_PROJECT_NAME` was exported in the shell. That is now fixed by naming each project explicitly with `env -u`.
- **`make check`** on the rebased branch: ruff and format clean, mypy clean, 463 pytest passed, web lint, format and typecheck clean, 298 vitest passed.
- Code review (Standards and Spec) fixes landed in the second commit. Skipped as minor: two setups started at the same moment could pick the same ports, and two first-time Playwright installs in `$TMPDIR` could race.

## Completion

- Completed: 2026-11-13
- Commit: <filled in after merge>
