# AI Companion

See `ABOUT.md` for the product overview.

## Agent skills

### Issue tracker

Issues are tracked as local markdown files under `.scratch/<feature>/` (no PR triage surface). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### UI design

The Dashboard UI design lives in `docs/design/`: `zeph-product.html` (User pages) and `zeph-admin.html` (admin area). Build pages from these; ignore anything tagged "Later".

## How I want you to work (process)

- **Plan before large changes.** For anything non-trivial, outline the approach first.
- **Small, reviewable steps.** Prefer incremental edits over sweeping rewrites.
- **Verify, don't assume.** Run the relevant command and report the real result.
- **Ask when genuinely blocked** on a decision only I can make; otherwise pick the
  sensible default, state it, and proceed.
- **Always be concise and clear in your responses**. Speak in plain simple english with no jargon or fancy words. No need say many words when few can do trick.
- **Don't stage, commit or push** unless I ask.

---

## Coding standards

### All code

- **Always** prefer simple code over complex over optimised code. Code should be written in a manner where the next person who reads it can understand clearly what we are trying to accomplish.
- Use absolute path imports instead of relative
- Keep functions focused; prefer pure functions and dependency injection over globals.
- Function and variable names MUST be clear and describe what they do or hold.
- No inline comments. If comments are absolutely needed, then put them in the function's docstring.
- Match the style of surrounding code — naming, comment density, structure.
- No secrets, API keys, or tokens in code or commits. Read them from `.env`.
- New code comes with tests, and isn't done until that language's checks pass — say so explicitly, with output, if any of them fail.
- Follow the ports-and-adapters pattern (https://8thlight.com/insights/a-color-coded-guide-to-ports-and-adapters)

### Python (backend, `src/`)

- Type-annotate all public functions; `mypy` must pass on `src/`.
- Use UV for package and virtual env management
- All methods _MUST_ have _google-style docstrings_ describing in concise manner what the method does, what parameters it takes and what it returns
- Read secrets and settings via `config.py`.
- Checks: `pytest`, `ruff`, `ruff format` and `mypy`.

### TypeScript / Next.js (Dashboard, `web/`)

- TypeScript only, no plain `.js` files. `strict` mode on; no `any` — use `unknown` and narrow it.
- Use pnpm for packages.
- Absolute imports through the `@/` alias (e.g. `@/lib/api-client`), never `../`.
- All exported functions and components _MUST_ have _TSDoc_ comments (`/** ... */`) describing in concise manner what it does, its parameters (`@param`) and what it returns (`@returns`).
- Use the App Router. Server Components by default; add `"use client"` only when a component needs state, effects or browser APIs.
- One component per file, named in PascalCase; hooks start with `use`.
- The Dashboard holds no business logic — it calls the backend API. All backend calls go through one API client module, so pages never call `fetch` directly.
- Clerk is used only inside auth-related files (middleware, sign-in/up pages, the auth helper); other code asks the auth helper for the current User.
- Read settings and public keys from environment variables through one typed `env` module, not `process.env` scattered around.
- Checks: `pnpm lint` (ESLint), `pnpm format:check` (Prettier), `pnpm typecheck` (`tsc --noEmit`) and `pnpm test` (Vitest + React Testing Library).

---

## Development workflow

Every piece of work — feature, refactor, or bug — gets an issue file in `.scratch/<feature>/issues/` **before** code changes. The issue file is the cross-session anchor: status, decisions, and blockers live there, not in chat history.

**New feature:**

1. `/grill-with-docs` — sharpen the idea; ADRs and `CONTEXT.md` updates land as decisions are made. (Skippable for small, well-understood work.)
2. `/to-prd` — synthesize the conversation into `.scratch/<feature>/PRD.md`.
3. `/to-issues` — break into tracer-bullet vertical slices with `Blocked by:` dependencies.
4. Per issue, on a branch: `/implement <issue path>` — TDD at agreed seams, quality gates, then `/code-review`.
5. `/verify` (or `/run`) — confirm the change actually works in the running app, not just that tests pass. Skipping this is how green tests ship broken behaviour.
6. `/post-implement` — verify acceptance criteria with evidence, mark `completed`, archive. Then `/domain-modeling` if the change moved the domain model (new terms, decisions) so `CONTEXT.md`/ADRs don't drift.

**Improve existing code:** `/simplify` for diff-scoped cleanup; `/improve-codebase-architecture` (with `/codebase-design` vocabulary) for structural work. Once scoped, funnel into an issue and follow steps 4–6 above — refactors get issues too, and get verified too.

**Debugging:** `/file-bug` to record it as an issue → `/diagnosing-bugs` (build a tight pass/fail feedback loop before touching code) → fix test-first with `/tdd` → `/run` the fix in the running system → `/code-review` → `/post-implement`, recording the confirmed hypothesis in the archived issue.

**What counts as a bug (important):** a bug is a defect in **already-implemented, shipped code** — the running system crashes, throws, or logs an error when exercised. Those get filed with `/file-bug`. A defect in code being written _right now_ (a broken function in the current diff, a failing test you just introduced) is **not** filed — fix it in place as part of finishing that work. When the user mentions a bug, this is the distinction to apply before reaching for `/file-bug`.

**Session ritual:**

- **Start**: run `/triage` ("show me what needs attention") to re-orient on in-flight work. When the user asks "what's in flight?" or "where were we?", this is the answer.
- **End, work complete**: `/post-implement`, then the user commits the `.scratch/` status change (commit message convention: "updated tasks status").
- **End, mid-task**: append a status note under `## Comments` in the active issue file — where things stand, what's next, any open questions.

---

## Definition of done

A task is done when:

1. Code compiles / imports, and the change is **verified in the running app** (via `/run`) — not just green in tests.
2. New behavior has tests; for a bug fix, a test that was red before the fix and is green after.
3. Acceptance criteria on the issue are checked off with evidence, and you've reported what you changed and any caveats plainly.

---
