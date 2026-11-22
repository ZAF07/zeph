# 16 — Production deployment

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Run the MVP on one HostHatch VPS (NVMe 16 GB: 4 AMD EPYC cores of which 2 dedicated, 16 GB RAM, 75 GB NVMe; Debian 13) using the same Docker Compose file and images as local (ADR-0005). Only `.env` differs. This issue is the manual first setup; automatic deploys on push to the `production` branch come in `.scratch/mvp/issues/31-ci-cd-deploy-on-push.md`.

- **Caddy** runs as a Compose service under a `prod` profile, in front of the Dashboard and backend, with automatic HTTPS.
- **Profiles are switched on in `.env`** through `COMPOSE_PROFILES`, so a plain `docker compose up` does the right thing everywhere:
  - local `.env`: `COMPOSE_PROFILES=local,eval` (ngrok and the eval-runner run, no Caddy)
  - prod `.env`: `COMPOSE_PROFILES=prod` (Caddy runs, no ngrok, no eval-runner)
- **Only Caddy is reachable from the internet** (ports 80 and 443). Postgres, backend and web publish their ports on a host address set in `.env` (`127.0.0.1` in prod). Docker bypasses `ufw`, so a firewall alone does not protect them.
- **`NEXT_PUBLIC_API_URL`** in the prod `.env` is the production domain. It is baked into the Dashboard at build time.
- **Server setup** is done (`.scratch/mvp/issues/archive/32-set-up-the-vps.md`): Docker Engine, an admin user `zaf` (sudo), a `deploy` user (Docker only, no sudo), key-only SSH with root login off, `ufw` allowing 22/80/443, 4 GB swap. The DuckDNS name points at the server (`.scratch/mvp/issues/archive/33-free-domain-on-duckdns.md`). The repo is cloned as `deploy` at `~/zeph`, on the `production` branch only (`git clone -b production --single-branch`), in issue 35.
- **Restart policy:** every long-running service has `restart: unless-stopped`, so the app comes back by itself after a reboot or a Docker upgrade.
- **Backups:** a nightly `pg_dump` cron job for `deploy`, with the dump copied off the server to Cloudflare R2 with `rclone copy` to `r2:zeph-backups` (remote and bucket already set up in issue 34; the bucket deletes files older than 30 days). rclone is the current release from rclone.org: Debian's packaged rclone is too old for R2 (`501 Not Implemented` on upload).

A short deployment guide covers first setup, updating by hand, and backups.

`docker-compose.yml` is a shared file; mention the changes in the PR.

## Acceptance criteria

- [x] The same Compose services and images run in production; only `.env` differs
- [x] `COMPOSE_PROFILES` in `.env` controls which services run: the eval-runner only with `eval`, Caddy only with `prod`; plain `docker compose up` locally still starts the eval-runner
- [x] Caddy serves the Dashboard and backend over HTTPS with automatic certificates
- [x] From outside the server, only ports 80 and 443 answer; Postgres (5432), backend and web ports do not (checked with `nc` from another machine)
- [x] The live Dashboard calls the production API domain, not localhost
- [x] The Telegram webhook is registered to the production domain and verified with the secret token
- [x] Postgres data is on a persistent volume, with a documented backup and restore command; the nightly backup is copied to `r2:zeph-backups`
- [x] Every long-running service has `restart: unless-stopped`; after `sudo reboot` the app comes back without a manual `docker compose up`
- [x] A deployment guide covers first setup (the server steps from issue 32, DuckDNS, R2 and rclone, clone, prod `.env`), updating by hand (`git pull` then `docker compose up -d --build`, automated later by issue 31), and backups
- [x] The deployment guide links `docs/RESET_TELEGRAM_TOKEN_GUIDE.md`: reset the bot token when it leaks or might have (BotFather revoke → update `.env` → `make restart`), not on a schedule
- [x] Verified on the live server: sign up, connect Telegram, receive the welcome message

## Blocked by

- `.scratch/mvp/issues/archive/01-walking-skeleton.md`

## Comments

- 2026-11-21: No real domain yet (final product name not chosen). Start on a free DuckDNS subdomain; Caddy still gets a Let's Encrypt certificate for it. The domain lives only in `.env` (Caddy site address, `NEXT_PUBLIC_API_URL`), so switching later is: update `.env`, `docker compose up -d --build`, re-register the Telegram webhook. Clerk stays on its development instance until the real domain exists (a Clerk production instance needs DNS records on a domain we own). Off-server backups go to Cloudflare R2.
- 2026-11-21: Server OS: Debian 13 or Ubuntu 24.04, both fine. On Debian, install and enable `unattended-upgrades` for automatic security updates.
- 2026-11-22: The hands-on server work is split into human issues: 32 (VPS setup), 33 (DuckDNS), 34 (R2 backups), 35 (first deploy). This issue builds the repo side (Caddy service, `Caddyfile`, bind addresses, backup script, deployment guide). The live-server criteria here are checked through issue 35. The Caddyfile reads the domain from `PRODUCTION_DOMAIN`.
- 2026-11-22: Repo side done and merged: Caddy service and `Caddyfile` (prod profile; `/api/*`, `/telegram/*`, `/health` to the backend, the rest to the Dashboard, one domain), eval-runner under the `eval` profile, Postgres/backend/web ports on `PORT_BIND_ADDRESS` (default `127.0.0.1`), `restart: unless-stopped` on every service, `scripts/backup.sh`, `docs/DEPLOYMENT_GUIDE.md`. Checked in a running worktree stack with `COMPOSE_PROFILES=eval,prod PRODUCTION_DOMAIN=localhost`: `docker compose config --services` gives the right services per profile; through Caddy `/health` 200, `/api/me` 401, `/telegram/webhook` 401 (bad secret), `/` the Dashboard, http redirects to https; from the LAN address only 443 answered (3010/5442/8010 closed); every container's restart policy is `unless-stopped`; `scripts/backup.sh` made a real `pg_dump`, and the guide's restore command brought back a dropped table (exit 0). `make check` green (1491 Python, 899 web tests).
  Still open, all live-server checks done through issue 35: Let's Encrypt certificate, `nc` from outside, live Dashboard calling the prod domain, `getWebhookInfo`, reboot, live sign-up. The nightly backup cron needs `sudo apt install -y make cron` on the VPS first (neither is installed), then the crontab line from the guide (issue 34 step 8).
- 2026-11-22: Live checks from a laptop against `https://zeph-dev.duckdns.org` (the DuckDNS name; issue 35's `zeph-beta` was an example): certificate issued by Let's Encrypt (CN=YE1) for `zeph-dev.duckdns.org`, valid to 2027-02-20; `/health` gives `{"status":"ok"}`; http redirects 308 to https; Dashboard 200. `nc` from the laptop: 80 and 443 open; 3000, 5432, 8000 and 2019 closed. The live Dashboard's JS holds `https://zeph-dev.duckdns.org` and no `localhost:8xxx`. `getWebhookInfo`: url `https://zeph-dev.duckdns.org/telegram/webhook`, no `last_error_message`, 0 pending; a POST to the webhook with no secret or a wrong one gets 401.
  Still open: the first nightly backup in `r2:zeph-backups` (cron installed for 19:30 UTC), `sudo reboot` brings the app back, and the live sign-up / connect Telegram / welcome message.
- 2026-11-22: Live sign-up confirmed by the owner: signed in on the live Dashboard, and a second User (a friend) signed up and is using Zeph through Telegram. Still open: the first nightly backup in `r2:zeph-backups`, and `sudo reboot` brings the app back.
- 2026-11-22: Last two checks confirmed by the owner on the live server: after `sudo reboot` the app came back by itself (`docker compose ps` all up), and the cron job ran `scripts/backup.sh` (set to run a minute ahead for the test) and the dump appeared in `r2:zeph-backups`. The job is back on its nightly time, 19:30 UTC.

## Completion

- Completed: 2026-11-22

## Commits

- `7429bf2` - Production deployment: Caddy under prod profile, eval-runner under eval, ports on 127.0.0.1, restart policies, nightly R2 backup script and deployment guide (issue 16)
- `9342276` - Review fixes for issue 16; add prod seed step to issue 35
- `093fe77` - Issue 16: record repo-side progress and evidence
- `7dc475a` - Deployment guide: nightly backup at 19:30 UTC (03:30 at UTC+8)
- `cddc852` - Deployment guide: one cron command that replaces the backup job
- `802b6b1` - Issue 16: live-server checks for HTTPS, ports, API domain and webhook
- `afd0c59` - Issue 16: live sign-up confirmed
- `6696274` - Archive issues 16 and 34: production deployment and nightly R2 backup done
