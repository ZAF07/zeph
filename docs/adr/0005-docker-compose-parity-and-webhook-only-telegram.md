# Docker Compose everywhere, Telegram webhook only

Every service (backend, Dashboard, Postgres with pgvector) runs in containers defined by Docker Compose, and the same images run locally and in production; only `.env` differs. Telegram always uses a webhook — locally through an ngrok tunnel — rather than polling in development, so the path tested locally is the path that runs in production.

## Consequences

- Local development needs an ngrok account and auth token, and the webhook URL changes when the tunnel restarts unless a fixed ngrok domain is used.
