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
4. **Write the prod `.env`:** `cp .env.example .env`, then fill it in by hand following the deployment guide from issue 16. The domain-related values (using your DuckDNS name):
   ```
   COMPOSE_PROFILES=prod
   PRODUCTION_DOMAIN=zeph-beta.duckdns.org
   WEBHOOK_BASE_URL=https://zeph-beta.duckdns.org
   NEXT_PUBLIC_API_URL=<as the guide says>
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

## Acceptance criteria

- [ ] `production` branch exists on GitHub
- [ ] Repo cloned on the VPS with only `production`
- [ ] Dashboard loads over HTTPS on the DuckDNS name
- [ ] `getWebhookInfo` shows the DuckDNS URL and no errors
- [ ] Sign up, connect Telegram, welcome message received

## Blocked by

- `.scratch/mvp/issues/16-production-deployment.md`
- `.scratch/mvp/issues/32-set-up-the-vps.md`
- `.scratch/mvp/issues/33-free-domain-on-duckdns.md`
