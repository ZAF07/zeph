# 01 — Run the Dashboard as a production build

Status: completed

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

- [x] The web image builds the Dashboard at image build time and serves it with `next start`; no development server runs in the container
- [x] `NEXT_PUBLIC_*` values come from `.env` through Compose at build time; no secret is baked into the image
- [x] The web server still refuses to start when `CLERK_SECRET_KEY` is missing
- [x] Measured in the running stack: no page shows a first-visit compile, sidebar clicks reach content in ~50 ms, web container memory is ~200 MB (paste the numbers)
- [x] Sign-in, User pages and admin pages work in the running stack
- [x] ADR-0005 (or a new ADR) records that the Dashboard image is a production build, and how to run `pnpm dev` outside Docker for quick UI work
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass

## Blocked by

None - can start immediately

## Comments

### 2026-11-17 — done (agent, branch `dashboard-speed-01-production-build`)

What changed:
- `web/Dockerfile`: takes `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` as build args, runs `pnpm build`, serves with `pnpm start --hostname 0.0.0.0`.
- `docker-compose.yml`: the web service passes the two `NEXT_PUBLIC_*` keys from `.env` as build args; its run-time environment is only `CLERK_SECRET_KEY`.
- `web/next.config.ts` is now a phase function (`buildNextConfig(phase)`); `checkServerSettings(phase)` in `web/src/env.ts` skips the secret check only for `PHASE_PRODUCTION_BUILD`, so `next start` and `next dev` still refuse to start without it. Tests in `web/src/env.test.ts`.
- ADR-0005: the Dashboard image is a production build; `NEXT_PUBLIC_*` are build args (a change needs a rebuild, an empty one fails the build); no secret in the image; no hot reload, `make restart` after changes; how to run `pnpm dev` on the host on the same port.

Evidence per acceptance criterion (worktree stack 3010/8010/5442):
- Production build, no dev server: image build log lists every route from `next build`; `ps` in the web container shows `next start --hostname 0.0.0.0` and `next-server (v15.5.29)`, no `next dev`; web logs have 0 "compil" lines after visiting every page.
- `NEXT_PUBLIC_*` from `.env`, no secret baked in: the image was built with no `CLERK_SECRET_KEY` anywhere; inside the image `env` has no `CLERK_SECRET_KEY`, `grep -rlF <secret>` over `/app/.next` and `/app/src` finds 0 files, `docker history --no-trunc` has 0 matches. `NEXT_PUBLIC_API_URL` in the image is the worktree's `http://localhost:8010`.
- Refuses to start without the key: `docker run -e CLERK_SECRET_KEY= <web image>` → `Error: Missing required setting in .env: CLERK_SECRET_KEY` at `checkServerSettings`, `pnpm` exit code 1. Unit tests: refuses for `PHASE_PRODUCTION_SERVER`, starts with the key, builds without it.
- Measured (Playwright, run-dashboard Admin session, script `measure.mjs`: time to `main` having content and no `[aria-busy=true]`; 21 User and admin pages; machine load ~6 — a run at load 12–18 while other stacks were busy was 2–3× slower and is not counted):
  - First visit vs warm full load: 916–1125 ms first, 930–1122 ms warm (one 2353 ms outlier on `/`) — no first-visit compile. Full loads still include Clerk's own ~350 ms page check (issue 02).
  - Sidebar clicks, two runs: min 39 / median 57 / max 162 ms and min 37 / median 56 / max 135 ms; the first click (`/memories`) is the slowest, the rest 42–71 ms.
  - Web container memory: 181–191 MiB (dev mode on the main stack: 629 MiB–1.5 GB).
- Sign-in, User pages, admin pages: the run-dashboard session signed in through Clerk; all 21 pages (Home, Memories, Check-ins, Account, and all 17 admin pages) loaded with their heading and no page errors; screenshots of Home and Knowledge looked right; a signed-out visit to `/admin/users` landed on `/sign-in` with the sign-in form.
- ADR-0005: records it; the host `pnpm dev` steps were run in the worktree (web container stopped, `pnpm dev --port 3010`, `/admin/users` loaded signed in) and the container started again.
- Checks: `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 66 files / 458 passed. Backend (no Python changes): ruff, ruff format --check, mypy clean, pytest 1183 passed.

Caveats:
- `docker-compose.yml` is a shared file; only the web service changed.
- The first `pnpm build` in the image adds ~40 s to `make restart`.
