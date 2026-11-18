# 15 — Redesign: restyle uncovered admin pages

Status: ready-for-agent

Lane: whichever agent is free first. README slice: none (decided in grilling: "slice 16").

## Parent

`.scratch/redesign/PRD.md`

## What to build

Restyle the admin pages no reference or template covers, so nothing is left in the old theme:

- eval run, and eval result inside a run
- eval case list for one eval, new case and edit case (the case editors, ADR 0014)
- new eval, judge, costs, case history
- Knowledge Document detail
- model-call trace

Use **only the tokens and existing parts** (cards, field rows, tables, save bar, states, card-list parts). Don't change layout order, behaviour or copy, except where the old theme's wording is replaced by a part's fixed copy. There's no pixel test. The code editor theme must use the tokens too.

## Acceptance criteria

- [ ] No old-theme colours or Tailwind default palette classes remain on any admin page (search shown).
- [ ] Screenshots of each page at both widths are attached.
- [ ] A list of every choice the agent made itself (spacing, which part, editor colours) is in this issue for Zaf.
- [ ] Every page works as before (the existing tests pass, and a `/run` check covers one eval run and one case edit). **Don't start a real eval run without asking Zaf, because evals cost money.**

## Blocked by

- `.scratch/redesign/issues/11-other-table-pages.md`
- `.scratch/redesign/issues/12-form-pages.md`
- `.scratch/redesign/issues/13-card-list-pages.md`

## Rules for every redesign issue

- Read `web/design/README.md` in full, then every reference file named here at both widths, before coding. The README wins on look, copy and behaviour. Where it and this issue differ, stop and ask. Its "When to stop and ask" list applies.
- Build so the computed styles equal the reference's inline styles. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory. Use only the tokens (arbitrary values like `gap-[22px]` where no token exists).
- Never change anything in `web/design/` (`LIMIT`, masks, baselines, references), except the one image swap and baseline rebuild in issue 01.
- Own worktree (`make worktree-setup`), own branch, own PR. Run the pixel test with `BASE_URL=http://localhost:$WEB_PORT`, `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, and the two session files from issue 01's script.
- **Parallel work.** Two agents work at once. Put this issue's sample data in its own fixture file for its page area, and don't edit another area's file. Only issue 01 edits the theme, font, fixture switch and pixel-test setup. Only issue 02 edits the sidebar and menu. Only issue 08 edits the middleware. If you need a change in one of those, stop and ask.
- Use the shared state parts from issue 03 (empty, loading, error, saved, confirm) for every state this issue's pages show (from issue 04 on).
- Existing behaviour, API calls, Clerk logic and tests stay as they are. Update a test only where the markup it checks has changed.
- Before the PR: `git fetch origin && git rebase origin/main`, then re-run this issue's pixel test and checks.

## Done when (for every redesign issue)

- [ ] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [ ] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [ ] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [ ] `/code-review` run, and findings fixed or answered.

## Comments
