# Deploy on push to production, built on the server

Every push to the `production` branch runs `make check` on GitHub Actions; if it passes, the workflow logs into the VPS over SSH, moves the server's clone to exactly the commit that was checked, and runs `docker compose up -d --build`, then calls the live `/health`. `main` stays the everyday branch; merging `main` into `production` is how a change goes live. The server builds its own images, so build-time values like `NEXT_PUBLIC_API_URL` come from its `.env`, and GitHub holds only SSH connection details, never app secrets. Only one deploy runs at a time; a newer push waits instead of cancelling a deploy halfway.

## Considered Options

- **Deploy on push to `main`.** Fewer branches, but every docs or issue-file commit would go live and rebuild the server, and there would be no step between "merged" and "live".
- **Build images in CI and pull them from GHCR.** Faster deploys and no build load on the server, but `NEXT_PUBLIC_*` values would have to live in GitHub, and a registry adds tokens and setup. Revisit if builds on the 2-core server get slow.
- **`git pull` the branch tip.** Simpler, but a commit pushed while an earlier run is checking would go live before its own checks ran.

## Consequences

- Each deploy has a few seconds of downtime while containers restart. Fine before launch.
- A failed build on the server leaves the running containers on the old version.
- Roll back by reverting on `main` and merging into `production`. Steps, secrets and timings are in `docs/DEPLOYMENT_GUIDE.md`.
- The workflow's `PRODUCTION_URL` must change with the domain.
