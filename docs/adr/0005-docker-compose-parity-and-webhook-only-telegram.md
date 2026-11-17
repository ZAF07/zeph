# Docker Compose everywhere, Telegram webhook only

Every service (backend, Dashboard, Postgres with pgvector) runs in containers defined by Docker Compose, and the same images run locally and in production; only `.env` differs. Telegram always uses a webhook — locally through an ngrok tunnel — rather than polling in development, so the path tested locally is the path that runs in production.

## Consequences

- Local development needs an ngrok account and auth token, and the webhook URL changes when the tunnel restarts unless a fixed ngrok domain is used.
- The Dashboard image is a production build: `next build` runs when the image is built and the container serves it with `next start`, locally and in production alike. Dev mode compiled each page on its first visit and used ~1.5 GB of memory; the build has no first-visit compile and uses ~200 MB.
- `NEXT_PUBLIC_*` values are inlined by `next build`, so Compose passes them from `.env` as build args. `CLERK_SECRET_KEY` is never baked into the image: it is given only at run time, and the server refuses to start without it.
- There is no hot reload in the container; run `make restart` after code changes. For quick UI work, stop the container and run the dev server on the host on the same port (Clerk and the backend only accept the Dashboard's own address, `DASHBOARD_URL`):

  ```bash
  docker compose stop web
  cd web && set -a && . ../.env && set +a && pnpm dev --port "${WEB_PORT:-3000}"
  ```

  `make restart` brings the container back.
