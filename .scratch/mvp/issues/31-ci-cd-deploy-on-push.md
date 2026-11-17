# 31 — CI/CD: deploy on push to main

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

A GitHub Actions workflow that runs on every push to `main`:

1. **Checks:** run `make check`. If any check fails, nothing is deployed.
2. **Deploy:** SSH into the VPS as the `deploy` user, then in the repo run `git pull` and `docker compose up -d --build`. The server builds the images itself, so build-time values like `NEXT_PUBLIC_API_URL` come from the server's own `.env`. Migrations run on backend start (`prestart`).
3. **Health check:** call the live backend's `/health`. If it doesn't answer, the run fails.

GitHub holds only the SSH key, host and user as secrets. All app secrets stay in `.env` on the server.

Each deploy brings a few seconds of downtime while containers restart. That is fine before launch. Building images in CI and pulling them from GHCR is out of scope; revisit it if builds on the server get slow.

## Acceptance criteria

- [ ] A push to `main` runs `make check`; a failing check stops the run before deploy
- [ ] When checks pass, the workflow deploys over SSH with `git pull` and `docker compose up -d --build`
- [ ] The workflow fails if the live `/health` check doesn't answer after deploy
- [ ] GitHub secrets hold only the SSH key, host and user; no app secrets in GitHub or the repo
- [ ] Only one deploy runs at a time (a newer push waits or cancels the older run)
- [ ] The deployment guide explains the workflow, the GitHub secrets to set, and how to roll back (deploy an older commit)
- [ ] Verified live: push a small visible change to `main` and see it on the production Dashboard

## Blocked by

- `.scratch/mvp/issues/16-production-deployment.md`
