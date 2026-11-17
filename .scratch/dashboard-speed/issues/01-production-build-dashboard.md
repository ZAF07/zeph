# 01 — Run the Dashboard as a production build

Status: ready-for-agent

## What to build

The Dashboard image runs the Next.js development server (`pnpm dev`), and per ADR-0005 the same image runs in production. Development mode compiles each page on its first visit (0.4–3.5s seen in logs), ships unoptimised JavaScript and sits at ~1.5 GB memory idle.

Change the web image so it builds the Dashboard once at image build time (`next build`) and serves it with `next start`, locally and in production alike. Local stays a mirror of production: same image recipe, only `.env` differs.

Decisions already made:

- `NEXT_PUBLIC_*` values are inlined at build time, so Docker Compose passes them to the web image build from `.env` (build args), keeping "only `.env` differs".
- The Clerk secret key must not be baked into the image. The server-settings check in the Next.js config must not demand it during the build; it still fails loudly at server start when the key is missing.
- Hot reload in the container goes away; code changes need `make restart`. For quick UI work, document running `pnpm dev` on the host outside Docker.

Measured before (dev mode, main stack, signed-in Admin, warm pages) vs a throwaway production build of the same code:

| | Dev mode | Production build |
|---|---|---|
| Sidebar click to content | 105–264 ms | 33–153 ms |
| Full page load to content | 1.3–2.3 s | 0.9–1.1 s |
| First visit to a page | +0.4–3.5 s compile | none |
| Web container memory | 1.5 GB | ~200 MB |

Measure with a Playwright script (run-dashboard session) that records time to content (no `[aria-busy=true]` left in `main`) for full loads and sidebar clicks.

## Acceptance criteria

- [ ] The web image builds the Dashboard at image build time and serves it with `next start`; no development server runs in the container
- [ ] `NEXT_PUBLIC_*` values come from `.env` through Compose at build time; no secret is baked into the image
- [ ] The web server still refuses to start when `CLERK_SECRET_KEY` is missing
- [ ] Measured in the running stack: no page shows a first-visit compile, sidebar clicks reach content in ~50 ms, web container memory is ~200 MB (paste the numbers)
- [ ] Sign-in, User pages and admin pages work in the running stack
- [ ] ADR-0005 (or a new ADR) records that the Dashboard image is a production build, and how to run `pnpm dev` outside Docker for quick UI work
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass

## Blocked by

None - can start immediately

## Comments
