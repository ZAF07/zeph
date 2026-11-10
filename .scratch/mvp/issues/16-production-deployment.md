# 16 — Production deployment

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Run the MVP on a single small VPS using the same Docker Compose setup and images as local (ADR-0005), with Caddy in front for automatic HTTPS. The Telegram webhook points at the production domain. A short deployment guide covers first setup, updating to a new version, and backing up Postgres.

## Acceptance criteria

- [ ] The same Compose services and images run in production; only `.env` differs
- [ ] Caddy serves the Dashboard and backend over HTTPS with automatic certificates
- [ ] The Telegram webhook is registered to the production domain and verified with the secret token
- [ ] Postgres data is on a persistent volume, with a documented backup and restore command
- [ ] A deployment guide covers first setup, updating, and backups
- [ ] Verified on the live server: sign up, connect Telegram, receive the welcome message

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`
