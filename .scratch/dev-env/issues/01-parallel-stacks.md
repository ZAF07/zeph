# 01 — Run a stack per worktree, side by side

Status: in-progress

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

- [ ] Two worktrees run their full stacks at the same time on different ports, each with its own database, and the main folder still runs on 3000/8000/5432 with no changes to its `.env`
- [ ] Sign-in works on a worktree's Dashboard port (Clerk dev instance), and its Dashboard talks to its own backend (no CORS errors)
- [ ] Only the main stack registers the Telegram webhook; a worktree stack answers an update posted to its own webhook
- [ ] Two agents can run `start-session.sh`, `drive.sh` and `cleanup.sh` in different worktrees at the same time without touching each other's session or test user
- [ ] `make worktree-setup` sets up a fresh worktree in one step and never edits the main folder
- [ ] `make worktree-teardown` leaves nothing of the worktree's stack behind (containers, images, network, volume) and refuses to run in the main folder
- [ ] `make check` passes
- [ ] Verified by running two stacks side by side and driving both Dashboards with the run scripts

## Notes

- Each stack runs Postgres, the backend (with its embedding model) and the Next dev server; three or four at once will use a lot of RAM.
- If two agents ever need to test from a phone at once, a second test bot from BotFather (its own token, webhook and ngrok domain) is the way; out of scope here.
- Shared files this touches: `docker-compose.yml`, `Makefile`, `src/companion/prestart.py` and `config.py`, the run-dashboard skill, `CLAUDE.md`.

## Blocked by

None.
