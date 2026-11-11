# 01 — Walking skeleton: sign up, connect Telegram, welcome message

Status: completed

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

- [x] `docker compose up` starts backend, Dashboard and Postgres (with pgvector extension) with no manual steps beyond filling `.env`
- [x] `.env.example` is committed and lists every MVP key with comments and no real values; `.gitignore` excludes `.env`
- [x] Copying `.env.example` to `.env` and filling it is the only setup step; Compose passes each service only its own keys, and the Dashboard never receives backend secrets
- [x] A missing required key stops startup with a clear message naming the key; keys for later issues are optional until those issues land
- [x] A new person can sign up on the Dashboard through Clerk; the backend creates a User keyed by the Clerk ID
- [x] The Dashboard shows a "Connect Telegram" button that opens Telegram with a one-time, expiring connection token
- [x] The Connect Telegram screen shows every state: link ready (QR code, `/start <code>` text, Open in Telegram), waiting for hello, connected, and link expired or already used with a "Get a new link" button
- [x] Sign-up and sign-in use Clerk's prebuilt components themed with the design tokens, and show the 18+ and Terms lines
- [x] Sending `/start <token>` makes the Telegram Connection and the Companion sends the seeded welcome message
- [x] An expired or already-used token gets a clear reply pointing back to the Dashboard to get a new link
- [x] A Telegram account already connected to one User cannot be connected to another
- [x] The Dashboard shows the Telegram Connection status
- [x] Webhook requests without the correct secret token header are rejected
- [x] Core code imports no Clerk, Telegram, or database libraries
- [x] Seam 1 tests cover the connection flow (success, expired, reused, already-linked) through the HTTP surface with fakes and a real Postgres container
- [x] `make check` exists and passes (pytest, ruff, ruff format, mypy; pnpm lint, format:check, typecheck, test)
- [x] Verified in the running app via `/run`: real sign-up, real Telegram connection, welcome message received

## Blocked by

None - can start immediately

## Comments

**2026-11-11 — implemented on branch `feat/01-walking-skeleton`.**

Decisions:
- The Clerk secret key also goes to the Dashboard's server, because Clerk's Next.js middleware needs it. It never reaches the browser, and all other secrets stay backend-only. Accepted by the owner and recorded in ADR-0001.
- A User is created on their first authenticated Dashboard API call (`GET /api/me` or any `/api` route). No Clerk webhooks are used.
- Connection token texts and the token lifetime (15 min) are seeded platform settings: `welcome_message`, `connection_token_invalid_reply`, `telegram_connected_elsewhere_reply`, `connection_token_ttl_minutes`. `{dashboard_url}` is filled in from `DASHBOARD_URL`.
- Tokens are claimed in one atomic step, so two requests can never both use one code. If the account that used a code sends it again (for example a Telegram retry), it gets the welcome again instead of "expired".
- When the Telegram account is already connected to another User, the token is marked `connected_elsewhere`, so the Dashboard can show that state (design state 5).
- The seed loader runs on every start but only adds missing keys, so Admin edits are never overwritten.
- The core's import ban (no adapter libraries) is enforced by `src/companion/core/ruff.toml`.

Caveats / follow-ups:
- The Dashboard container runs `pnpm dev`. The production build is issue 16.
- Vitest is pinned to 3.x and jsdom to 26.x, because the newer versions don't support Node 23.
- The Terms and Privacy links point to `/terms` and `/privacy`, which don't exist yet.
- The sidebar only shows Home until the later pages exist.
- The live "send a used code again" check wasn't done by hand. Seam 1 tests cover it.
- Review judgement calls not acted on: `prestart.py` builds the Postgres and Telegram pieces directly instead of choosing them from config; "token" means both the record and its code string; the error-card markup is repeated; the `build_*` adapter functions repeat the same if/else.
- Bug found during the live run and fixed: Clerk's API refuses Python's default user agent (403). The verifier now sends its own, and a key-fetch failure raises instead of turning into a silent 401.

## Completion

- Completed: 2026-11-11
- Commit: <to be filled in manually>
