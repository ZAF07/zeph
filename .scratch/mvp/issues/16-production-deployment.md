# 16 — Production deployment

Status: ready-for-agent

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

- [ ] The same Compose services and images run in production; only `.env` differs
- [ ] `COMPOSE_PROFILES` in `.env` controls which services run: the eval-runner only with `eval`, Caddy only with `prod`; plain `docker compose up` locally still starts the eval-runner
- [ ] Caddy serves the Dashboard and backend over HTTPS with automatic certificates
- [ ] From outside the server, only ports 80 and 443 answer; Postgres (5432), backend and web ports do not (checked with `nc` from another machine)
- [ ] The live Dashboard calls the production API domain, not localhost
- [ ] The Telegram webhook is registered to the production domain and verified with the secret token
- [ ] Postgres data is on a persistent volume, with a documented backup and restore command; the nightly backup is copied to `r2:zeph-backups`
- [ ] Every long-running service has `restart: unless-stopped`; after `sudo reboot` the app comes back without a manual `docker compose up`
- [ ] A deployment guide covers first setup (the server steps from issue 32, DuckDNS, R2 and rclone, clone, prod `.env`), updating by hand (`git pull` then `docker compose up -d --build`, automated later by issue 31), and backups
- [ ] The deployment guide links `docs/RESET_TELEGRAM_TOKEN_GUIDE.md`: reset the bot token when it leaks or might have (BotFather revoke → update `.env` → `make restart`), not on a schedule
- [ ] Verified on the live server: sign up, connect Telegram, receive the welcome message

## Blocked by

- `.scratch/mvp/issues/archive/01-walking-skeleton.md`

## Comments

- 2026-11-21: No real domain yet (final product name not chosen). Start on a free DuckDNS subdomain; Caddy still gets a Let's Encrypt certificate for it. The domain lives only in `.env` (Caddy site address, `NEXT_PUBLIC_API_URL`), so switching later is: update `.env`, `docker compose up -d --build`, re-register the Telegram webhook. Clerk stays on its development instance until the real domain exists (a Clerk production instance needs DNS records on a domain we own). Off-server backups go to Cloudflare R2.
- 2026-11-21: Server OS: Debian 13 or Ubuntu 24.04, both fine. On Debian, install and enable `unattended-upgrades` for automatic security updates.
- 2026-11-22: The hands-on server work is split into human issues: 32 (VPS setup), 33 (DuckDNS), 34 (R2 backups), 35 (first deploy). This issue builds the repo side (Caddy service, `Caddyfile`, bind addresses, backup script, deployment guide). The live-server criteria here are checked through issue 35. The Caddyfile reads the domain from `PRODUCTION_DOMAIN`.
