# 01 — Walking skeleton: sign up, connect Telegram, welcome message

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The thinnest end-to-end path through every layer: a person signs up on the Dashboard with Clerk, taps "Connect Telegram", opens the Companion in Telegram with a one-time link, and receives a welcome message. The welcome text comes from seed data, not code.

This slice also lays the foundations every later slice relies on:

- Docker Compose running the backend, the Dashboard and Postgres with pgvector — the same setup locally and in production (ADR-0005).
- Telegram webhook through ngrok locally, verified with Telegram's secret token header.
- Ports and adapters in place for the ones this slice touches: chat channel (Telegram), auth verifier (Clerk), repositories (Postgres), clock. Adapter choice and secrets read from `.env` (ADR-0003, ADR-0004).
- One `.env` at the repo root holds every secret and adapter choice. Docker Compose reads it and passes each service only the keys it needs (the Dashboard gets only public values). A committed `.env.example` lists every key the whole MVP needs — grouped, commented with what it's for and which issue first uses it, no real values — so the owner can copy it to `.env` and paste credentials once. Groups: Postgres; Clerk (secret key, publishable key); Telegram (bot token, bot username, webhook secret); ngrok (auth token, fixed domain); public URLs (webhook base URL, Dashboard API URL); DeepSeek (API key, from issue 02); Tavily (API key, from issue 09); adapter choice per port; initial Admin emails; production domain for Caddy (from issue 16). A `.gitignore` keeps `.env` out of git. Settings are read through `config.py` (backend) and the typed `env` module (Dashboard); only keys for parts already built are required, and a missing required key stops startup with a message naming it.
- A database migration tool and a seed-data loader that runs on first start (platform settings table with the welcome message).
- Test setup for seam 1: throwaway Postgres test container, FastAPI test client, fake chat channel that records sent messages, fake auth verifier, fake clock.
- `make check` running all Python and TypeScript checks listed in CLAUDE.md.
- The Dashboard's design tokens (colours, type, radius, spacing) from the Foundations screen of the product design, set up in the Tailwind theme so every later page uses them.
- Sign-up and sign-in use Clerk's prebuilt components, themed with those tokens through Clerk's appearance options — no custom auth form (ADR-0001).

## Design

- `docs/design/zeph-product.html`: Foundations, Sign up, Telegram Connection states, Dashboard sidebar

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] `docker compose up` starts backend, Dashboard and Postgres (with pgvector extension) with no manual steps beyond filling `.env`
- [ ] `.env.example` is committed and lists every MVP key with comments and no real values; `.gitignore` excludes `.env`
- [ ] Copying `.env.example` to `.env` and filling it is the only setup step; Compose passes each service only its own keys, and the Dashboard never receives backend secrets
- [ ] A missing required key stops startup with a clear message naming the key; keys for later issues are optional until those issues land
- [ ] A new person can sign up on the Dashboard through Clerk; the backend creates a User keyed by the Clerk ID
- [ ] The Dashboard shows a "Connect Telegram" button that opens Telegram with a one-time, expiring connection token
- [ ] The Connect Telegram screen shows every state: link ready (QR code, `/start <code>` text, Open in Telegram), waiting for hello, connected, and link expired or already used with a "Get a new link" button
- [ ] Sign-up and sign-in use Clerk's prebuilt components themed with the design tokens, and show the 18+ and Terms lines
- [ ] Sending `/start <token>` makes the Telegram Connection and the Companion sends the seeded welcome message
- [ ] An expired or already-used token gets a clear reply pointing back to the Dashboard to get a new link
- [ ] A Telegram account already connected to one User cannot be connected to another
- [ ] The Dashboard shows the Telegram Connection status
- [ ] Webhook requests without the correct secret token header are rejected
- [ ] Core code imports no Clerk, Telegram, or database libraries
- [ ] Seam 1 tests cover the connection flow (success, expired, reused, already-linked) through the HTTP surface with fakes and a real Postgres container
- [ ] `make check` exists and passes (pytest, ruff, ruff format, mypy; pnpm lint, format:check, typecheck, test)
- [ ] Verified in the running app via `/run`: real sign-up, real Telegram connection, welcome message received

## Blocked by

None - can start immediately
