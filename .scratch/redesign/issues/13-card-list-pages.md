# 13 — Redesign: card-list pages (Check-in Kinds template and the rest)

Status: ready-for-agent

Lane: A. README slice: 14.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Check-in Kinds** (`/admin/check-in-kinds`) to `AdminCheckInKinds`, `AdminCheckInKinds--all-folded` and `M-AdminCheckInKinds`. This is the **card-list template**:
  - The whole top row of a card toggles it, and the chevron points right when folded and down when open.
  - Several cards can be open at once. Expand all and Collapse all do what they say.
  - A card with unsaved edits shows the orange "Unsaved changes" tag on its folded row and keeps its text when folded.
  - It has the remove confirm, the empty, loading and couldn't-load states, and "could not save" in the save bar.
  - `?design=all-folded` renders every card folded in fixture mode.

  Build it as reusable parts.
- Then **Memory Categories, Needs, Moves, Sticker Library and Knowledge**, from the template. Each card keeps the order folded row, fields, save bar. Pages with more fields add field rows inside the open card and change nothing else. No pixel test for these. The Knowledge Document detail page is issue 15.
- If a page needs a part the template doesn't have, stop and ask. Fixture data goes in the admin-cards fixture file.

Refs: `AdminCheckInKinds`, `AdminCheckInKinds--all-folded`, `M-AdminCheckInKinds`.

## Acceptance criteria

- [ ] All three refs PASS.
- [ ] Tests: whole-row toggle, several open at once, Expand all / Collapse all, and the unsaved tag keeping text while folded.
- [ ] Each of the other five pages uses only card-list parts, with screenshots at both widths attached.
- [ ] Add, edit and remove work as before on every page (`/run`).

## Blocked by

- `.scratch/redesign/issues/02-shell.md`
- `.scratch/redesign/issues/03-shared-states.md`

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

- 2026-11-19 — Decisions (Zaf, asked at start):
  - Pixel test: as issues 09/10/12, no "Sample data" pill and no orange builder notes or samples. Checked by parts. The "Unsaved changes" tag on "A follow-up" comes from a real edit in the check script, not from fixture data.
  - Needs and Moves: the extra fields (ruled-out Moves checkboxes; "Needs a Feature" select and "asks a question" checkbox) are form-template field rows inside the open card. Move up/down are 44px round arrow buttons at the left of the save bar (as Helplines). The fallback Need has no Remove, and its bar says so.
  - Memory Categories: Name, Description, and "Always include" as a switch field row that still saves the moment it is flipped (as now), apart from the card's Save. Archive replaces Remove (with the confirm). Archived categories are a second "Archived" list of folded cards; their open card has only Restore.
  - Sticker Library: folded row has the picture, emoji, start of the note (or "Needs a note"). Open card: "When to use" field and the save bar (Save replaces save-on-leave), Remove with the confirm. "Add stickers" stays above the list as the adding box, with its tabs.
  - Knowledge: folded row has title, "source · tradition", status pill, added day. Open card: read-only lines (type, file name, failure reason); the bar has "Open document", Retry (if failed) and Delete with the confirm (replacing the browser confirm). The upload form stays above as the adding box.
