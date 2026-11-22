# 35 — First deploy to the VPS

Status: ready-for-human

## Parent

`.scratch/mvp/PRD.md`

## What to do

Put Zeph live for the first time, by hand.

1. **Create the `production` branch** from your laptop, once issue 16 is merged to `main`:
   ```
   git checkout main && git pull
   git push origin main:production
   ```
2. **Let the server read the repo** (skip if the repo is public). On the VPS as `deploy`:
   ```
   ssh-keygen -t ed25519 -f ~/.ssh/github_repo -N ""
   cat ~/.ssh/github_repo.pub
   ```
   On GitHub: repo → **Settings → Deploy keys → Add deploy key**, paste it, leave **write access off**. Then add to `~/.ssh/config` on the VPS:
   ```
   Host github.com
     IdentityFile ~/.ssh/github_repo
   ```
   Why read-only: the server only pulls code; it never pushes.
3. **Clone only `production`:**
   ```
   git clone -b production --single-branch git@github.com:ZAF07/zeph.git ~/zeph
   cd ~/zeph
   ```
   Why single-branch: the server can only ever pull `production`, so nothing from `main` goes live by mistake.
4. **Write the prod `.env`:** `cp .env.example .env`, then fill it in by hand following `docs/DEPLOYMENT_GUIDE.md` (step 5). The domain-related values (using your DuckDNS name):
   ```
   COMPOSE_PROFILES=prod
   PORT_BIND_ADDRESS=127.0.0.1
   PRODUCTION_DOMAIN=zeph-beta.duckdns.org
   WEBHOOK_BASE_URL=https://zeph-beta.duckdns.org
   NEXT_PUBLIC_API_URL=https://zeph-beta.duckdns.org
   DASHBOARD_URL=https://zeph-beta.duckdns.org
   ```
   Use new, strong values for `POSTGRES_PASSWORD` and `TELEGRAM_WEBHOOK_SECRET` (`openssl rand -hex 32`). Leave `NGROK_*` empty. Clerk: development keys for now (see issue 33).
   This file never goes into git; app secrets live only here.
5. **Start it:** `docker compose up -d --build` (first build takes a while).
6. **Check:**
   - `docker compose ps`: all services up, Caddy included, no ngrok or eval-runner
   - open `https://zeph-beta.duckdns.org` in the browser: padlock shows, Dashboard loads
   - the Telegram webhook registers itself on backend start from `WEBHOOK_BASE_URL`; check with `curl https://api.telegram.org/bot<token>/getWebhookInfo`
7. **Live test:** sign up, connect Telegram, get the welcome message.
8. **Seed with the local database** (platform settings, prompts and the rest, dumped from the main local stack on 2026-11-22). This **replaces everything** in the prod database, including the account made in step 7, so do it after the live test. As `deploy`, in `~/zeph`:
   ```
   ls ~/seed/   # seed-local-2026-11-22T055241Z.dump; also in r2:zeph-backups/seed/ until R2 deletes it after 30 days
   docker compose stop backend web
   docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < ~/seed/seed-local-2026-11-22T055241Z.dump
   docker compose start backend web
   ```
   Check: sign in on the Dashboard and the Admin pages show your local platform settings and prompts. Warnings like "does not exist, skipping" are fine.
   The dump includes your Telegram link, so from now on prod sends you Check-ins. Before restarting the local main stack, set `TELEGRAM_WEBHOOK_REGISTER=false` in its `.env`, or a local start moves the bot's webhook back to ngrok.

## Acceptance criteria

- [x] `production` branch exists on GitHub
- [x] Repo cloned on the VPS with only `production`
- [x] Dashboard loads over HTTPS on the DuckDNS name
- [x] `getWebhookInfo` shows the DuckDNS URL and no errors
- [x] Sign up, connect Telegram, welcome message received
- [x] Prod database seeded from the local dump; Admin pages show the local platform settings and prompts

## Blocked by

- `.scratch/mvp/issues/16-production-deployment.md`
- `.scratch/mvp/issues/archive/32-set-up-the-vps.md`
- `.scratch/mvp/issues/archive/33-free-domain-on-duckdns.md`

## Commits:

7902992
