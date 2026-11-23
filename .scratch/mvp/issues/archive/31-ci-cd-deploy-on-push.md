# 31 — CI/CD: deploy on push to production

Status: completed

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

- [x] A push to `production` runs `make check`; a failing check stops the run before deploy
- [x] When checks pass, the workflow deploys over SSH with `git pull` and `docker compose up -d --build`
- [x] The workflow fails if the live `/health` check doesn't answer after deploy
- [x] GitHub secrets hold only `SSH_KEY`, `SSH_HOST`, `SSH_USER` and `SSH_KNOWN_HOSTS`; no app secrets in GitHub or the repo; host key checking stays on
- [x] Only one deploy runs at a time (a newer push waits or cancels the older run)
- [x] The deployment guide explains the workflow, the GitHub secrets to set, and how to roll back (deploy an older commit)
- [x] Verified live: merge a small visible change into `production` and see it on the production Dashboard

## Blocked by

- `.scratch/mvp/issues/archive/16-production-deployment.md`
- `.scratch/mvp/issues/35-first-deploy.md`
- `.scratch/mvp/issues/36-github-secrets-for-auto-deploy.md`

## Comments

- 2026-11-21: Deploys trigger on the `production` branch, not `main`. `main` is the everyday branch; merging `main` into `production` is how a change goes live. The server clones only `production`.
- 2026-11-22: Built `.github/workflows/deploy.yml` (check job runs `make check`; deploy job `needs: check`, SSHs in with `StrictHostKeyChecking=yes` and the `SSH_KNOWN_HOSTS` secret, runs `git pull --ff-only && docker compose up -d --build`, then polls `$PRODUCTION_URL/health` 30 times, 5 s apart). `concurrency: deploy-production` with `cancel-in-progress: false`, so a newer push waits instead of cancelling a deploy halfway. The health URL is a workflow `env`, not a secret: the domain is public and already in the docs. Rollback is a `git revert` pushed to `production` (fast way: `git reset --hard` on the server). Locked by `tests/test_deploy_workflow.py`; `actionlint` passes.
- 2026-11-22: Review fixes: the deploy runs `git fetch origin production && git merge --ff-only $GITHUB_SHA`, so it ships exactly the commit that passed checks, not a newer tip pushed while checks ran. Rollback is a revert on `main` merged into `production`, which avoids reverting merge commits. The live domain is `zeph-dev.duckdns.org`; the guide and `.env.example` said `zeph-beta`, which doesn't resolve, so both were fixed. Decision recorded in ADR-0023.
- 2026-11-22: Live checks, all on the real server (runs are on the repo's Actions page):
  - Run 1 (`4be653b`, a lint error on `production` only): `Run checks` failed, `deploy` skipped, server stayed on `01b3a26`.
  - Run 2 (`c46a8e7`, the revert): checks 7m 50s, deploy 1m 50s, `Check the live backend answers` passed, server moved to `c46a8e7`, `web` recreated.
  - Run 3 (`ba73e28`): failed `pnpm format:check` on an unformatted marker page, deploy skipped. A real failure the gate caught.
  - Run 4 (`8f8af70`): `https://zeph-dev.duckdns.org/deploy-check.html` went from 404 to "Deploy check for issue 31. Delete me." The visible change was live.
  - Run 5 (`ef73d55`, rollback the guide's way: `git revert` on `main`, merge into `production`): the page went back to 404, `/health` answered `{"status":"ok"}`.
  - Run 6 (`c7ba53b`, empty commit pushed during run 5): the Actions page showed "waiting for another serialized run to finish" while run 5 was "currently running".
  - A `.txt` marker was tried first and 404'd: signed-out requests for `.txt` go through Clerk's `auth.protect()`, which 404s. That's expected app behaviour, not a deploy fault.
- 2026-11-22: Why a deploy takes ~10 min: the check job installs everything on a fresh 4-core runner and runs the 1498 Python tests (each test file with its own Postgres) and 899 web tests one after another; the deploy builds both images on the 2-core server. Possible speed-up later: run Python and web checks as parallel jobs and cache uv packages.

## Completion

- Completed: 2026-11-22

## Commits:

`afcce32` - Deploy on push to production: checks, SSH deploy, live health check (issue 31)
`594fb6a` - Deploy workflow review fixes: deploy the checked commit, merge-safe rollback, real domain zeph-dev (issue 31)
`84640bc`, `d7f4637`, `00fbc0f` - temporary live-check marker page; removed by `71f5332`, `23169a8`, `ea14ce1`
`4be653b`, `c46a8e7`, `c7ba53b` - live-check commits on `production` only (failing check, its revert, empty commit for the wait test)
`3e41855` - Archive issue 31: deploy on push verified live; ADR-0023; issue 34 cron checked
