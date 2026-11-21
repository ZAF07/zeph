# 16 — Production deployment

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Run the MVP on one OVHcloud VPS (VPS-2: 4 vCores, 8 GB RAM) using the same Docker Compose file and images as local (ADR-0005). Only `.env` differs. This issue is the manual first setup; automatic deploys on push to the `production` branch come in `.scratch/mvp/issues/31-ci-cd-deploy-on-push.md`.

- **Caddy** runs as a Compose service under a `prod` profile, in front of the Dashboard and backend, with automatic HTTPS.
- **Profiles are switched on in `.env`** through `COMPOSE_PROFILES`, so a plain `docker compose up` does the right thing everywhere:
  - local `.env`: `COMPOSE_PROFILES=eval` (the eval-runner runs, no Caddy)
  - prod `.env`: `COMPOSE_PROFILES=prod` (Caddy runs, no eval-runner)
- **Only Caddy is reachable from the internet** (ports 80 and 443). Postgres, backend and web publish their ports on a host address set in `.env` (`127.0.0.1` in prod). Docker bypasses `ufw`, so a firewall alone does not protect them.
- **`NEXT_PUBLIC_API_URL`** in the prod `.env` is the production domain. It is baked into the Dashboard at build time.
- **Server setup:** Docker Engine installed, a `deploy` user that can run Docker, the repo cloned on the `production` branch only (`git clone -b production --single-branch`), swap enabled, and the domain pointed at the server's IP.
- **Backups:** a nightly `pg_dump` cron job, with the dump copied off the server.

A short deployment guide covers first setup, updating by hand, and backups.

`docker-compose.yml` is a shared file; mention the changes in the PR.

## Acceptance criteria

- [ ] The same Compose services and images run in production; only `.env` differs
- [ ] `COMPOSE_PROFILES` in `.env` controls which services run: the eval-runner only with `eval`, Caddy only with `prod`; plain `docker compose up` locally still starts the eval-runner
- [ ] Caddy serves the Dashboard and backend over HTTPS with automatic certificates
- [ ] From outside the server, only ports 80 and 443 answer; Postgres (5432), backend and web ports do not (checked with `nc` from another machine)
- [ ] The live Dashboard calls the production API domain, not localhost
- [ ] The Telegram webhook is registered to the production domain and verified with the secret token
- [ ] Postgres data is on a persistent volume, with a documented backup and restore command; the nightly backup is copied off the server
- [ ] A `deploy` user can run Docker and the repo is cloned on the server (needed by issue 31)
- [ ] A deployment guide covers first setup (Docker Engine, `deploy` user, swap, domain, clone, prod `.env`), updating by hand (`git pull` then `docker compose up -d --build`, automated later by issue 31), and backups
- [ ] The deployment guide links `docs/RESET_TELEGRAM_TOKEN_GUIDE.md`: reset the bot token when it leaks or might have (BotFather revoke → update `.env` → `make restart`), not on a schedule
- [ ] Verified on the live server: sign up, connect Telegram, receive the welcome message

## Blocked by

- `.scratch/mvp/issues/archive/01-walking-skeleton.md`
