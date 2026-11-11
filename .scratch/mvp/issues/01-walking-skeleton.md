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
