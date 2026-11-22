# 31 — CI/CD: deploy on push to production

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

A GitHub Actions workflow that runs on every push to the `production` branch. `main` stays the everyday branch; going live means merging `main` into `production`.

1. **Checks:** run `make check`. If any check fails, nothing is deployed.
2. **Deploy:** SSH into the VPS (HostHatch NVMe 16 GB, Debian 13) as the `deploy` user, then in `~/zeph` run `git pull` and `docker compose up -d --build`. `deploy` can run Docker but not `sudo`, so the deploy must not need it. The server builds the images itself, so build-time values like `NEXT_PUBLIC_API_URL` come from the server's own `.env`. Migrations run on backend start (`prestart`).
3. **Health check:** call the live backend's `/health`. If it doesn't answer, the run fails.

GitHub holds only SSH connection details as secrets: the key, host, user, and the server's host key (`SSH_KNOWN_HOSTS`, so the workflow checks it is talking to the real server instead of turning host checking off). All app secrets stay in `.env` on the server.

Each deploy brings a few seconds of downtime while containers restart. That is fine before launch. The server has 2 dedicated cores, so building on it while the app runs is fine for now. Building images in CI and pulling them from GHCR is out of scope; revisit it if builds on the server get slow.

## Acceptance criteria

- [ ] A push to `production` runs `make check`; a failing check stops the run before deploy
- [ ] When checks pass, the workflow deploys over SSH with `git pull` and `docker compose up -d --build`
- [ ] The workflow fails if the live `/health` check doesn't answer after deploy
- [ ] GitHub secrets hold only `SSH_KEY`, `SSH_HOST`, `SSH_USER` and `SSH_KNOWN_HOSTS`; no app secrets in GitHub or the repo; host key checking stays on
- [ ] Only one deploy runs at a time (a newer push waits or cancels the older run)
- [ ] The deployment guide explains the workflow, the GitHub secrets to set, and how to roll back (deploy an older commit)
- [ ] Verified live: merge a small visible change into `production` and see it on the production Dashboard

## Blocked by

- `.scratch/mvp/issues/16-production-deployment.md`
- `.scratch/mvp/issues/35-first-deploy.md`
- `.scratch/mvp/issues/36-github-secrets-for-auto-deploy.md`

## Comments

- 2026-11-21: Deploys trigger on the `production` branch, not `main`. `main` is the everyday branch; merging `main` into `production` is how a change goes live. The server clones only `production`.
