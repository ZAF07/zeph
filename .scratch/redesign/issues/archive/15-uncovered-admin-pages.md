# 15 — Redesign: restyle uncovered admin pages

Status: completed

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
- the Safety page's Helplines table: move it onto the table-template parts (`DataTable`, so each row becomes a label-and-value card below 900px), keeping its add, edit, reorder and fallback behaviour as they are

Use **only the tokens and existing parts** (cards, field rows, tables, save bar, states, card-list parts). Don't change layout order, behaviour or copy, except where the old theme's wording is replaced by a part's fixed copy. There's no pixel test. The code editor theme must use the tokens too.

## Acceptance criteria

- [x] No old-theme colours or Tailwind default palette classes remain on any admin page (search shown).
- [x] Screenshots of each page at both widths are attached.
- [x] The Safety page's Helplines table shows each row as a label-and-value card on a phone, with no sideways scroll (screenshot at 390, and its existing tests pass, updated only for markup).
- [x] A list of every choice the agent made itself (spacing, which part, editor colours) is in this issue for Zaf.
- [x] Every page works as before (the existing tests pass, and a `/run` check covers one eval run and one case edit). **Don't start a real eval run without asking Zaf, because evals cost money.**

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

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments
- 2026-11-19 — Added from issue 11: the Safety page's Helplines table still scrolls sideways on a phone (noted in issue 12); the README wants table rows as cards there. Also: issue 11 already rebuilt the eval case list for one eval (`EvalCasesList`) from the table template, so that page only needs a check here, not a restyle.
- 2026-11-19 — Done (branch `redesign-15-uncovered-admin-pages`). What changed, the evidence, and every choice made, for Zaf:

### What changed
- Restyled with tokens and existing parts only: eval run (`EvalRunView`, `EvalRunGrid`, `EvalRunActions`, `EvalVariantCard`, `MakeLiveControl`, `EvalRunSnapshotDetails`), eval result trace (`CaseResultTraceView`, `CaseResultCard`), case editors (`EvalCaseForm`, `Shape*` fields, `EvalImageField`), new eval (`NewEvalRunForm`, `VariantOverridesEditor`, `SettingOverrideField`, `EvalRunEstimateNote`), Judge, Model Prices (`EvalCostsFields`), case history, Knowledge Document (`KnowledgeDocumentView`, details, replace file, text editor, toolbar, Markdown preview, review dialog), model-call trace (`ModelCallTraceView`, `ModelCallCard`, content), the shared form field styles, and the CodeMirror theme (`codemirror-theme.ts`, tokens only, no mixed colours). The admin gate's loading box is the shared `LoadingPanel` too.
- Helplines table is now `DataTable`, so each row is a label-and-value card below 900px. Add, edit, reorder and fallback work as before.
- Asked for by Zaf during the work: the eval run grid and the Model Prices table also show as `TableCards` below 900px (the table stays from 900px), and every browser `window.confirm` on these pages is now the shared `ConfirmDialog`: Helplines remove, Knowledge delete, replace file (when the text was edited), discard text, and the leave-with-unsaved-text guard on links.
- `EvalCasesList` (cases for one eval) was already rebuilt in issue 11; checked at both widths, nothing to change.

### Old-theme search (criterion 1)
Search of `web/src` for the old token names (`subtle`, `hover`, `code`, `ink-body/soft/muted`, `on-black-*`, `blue*`, `yellow*`, `orange-text`, `danger-tint/line/deep`, `text-h1/h2/h3/body/lead/eyebrow/caption`, `rounded-panel`), `bg-white`/`bg-black`/`text-ink` off cream, `font-bold`/`font-semibold`, and every Tailwind default palette class (`gray-500` etc.). What's left:
```
src/components/OnboardingGate.tsx:36   border-danger-line bg-danger-tint text-danger-deep   (User-side gate, not an admin page)
src/components/OnboardingGate.tsx:55   bg-subtle                                            (User-side gate, not an admin page)
src/components/SettingLabel.tsx:22-23  font-semibold, text-caption text-ink-muted           (nothing imports it: dead file)
src/components/TextChangesReview.tsx:56 bg-black/60                                         (black is a token; dialog backdrop)
```
No admin page uses old-theme or default-palette classes. `OnboardingGate` and the dead `SettingLabel` are outside this issue; worth a small follow-up.

### Checks
```
make check (rebased on origin/main a25b4cb):
  ruff: All checks passed! · ruff format: 499 files already formatted · mypy: Success: no issues found in 186 source files
  pytest: 1319 passed in 1303.38s
web, after rebasing on origin/main 8626479 (issue 14 merged; no backend change since the make check above):
  pnpm typecheck: tsc --noEmit (no errors) · pnpm lint: eslint . (no errors)
  pnpm format:check: All matched files use Prettier code style!
  pnpm test: Test Files 114 passed (114) · Tests 709 passed (709)
  /run after the rebase: eval run, Safety, Knowledge Document and Model Prices at 1280 and 390, overflow 0px, no page errors
```
No pixel test for this issue (no refs).

### /run evidence (worktree stack, copy of the main database)
- Real data: the 2 real Eval Runs, 3 Knowledge documents, model-call traces, 4 Helplines. The real runs had one passing case each, so a made-up run with two Variants (B overrides `connection_token_ttl_minutes`), a fail, an error and a long case key was added to the worktree's database copy only. **No real eval run was started.**
- Every page at 1280 and 390: page sideways overflow 0px on all 12 pages. Screenshots: `archive/15-screenshots/` (`eval-run`, `eval-result`, `eval-cases`, `case-new`, `case-edit`, `eval-new`, `judge`, `costs`, `case-history`, `knowledge-doc`, `model-call-trace`, `safety`, each `-1280` and `-390`).
- Eval run: picked "pebble-practice on Variant B" (table at 1280 and phone card at 390) → its try opened with the failed check; "What this run used" loaded the snapshot; "Full trace" opened the trace page (`flow-run-picked-1280.png`).
- Case edit: changed Mood to "nervous (run check)", Save case → "Saved. The next run uses it; past runs keep the case as it was."; reload showed the new value; put back to "nervous" (`flow-case-saved-1280.png`).
- Helplines at 390: rows as cards (`safety-390.png`); moved IMH down (order SOS, SCDF, IMH) and back up; Remove opened the dialog and "Keep it" closed it (`flow-helplines-moved-390.png`, `flow-helpline-remove-dialog-390.png`).
- Knowledge: Discard changes → dialog → Keep editing kept the edit, Discard dropped it; "← Knowledge" with unsaved text → dialog → Keep editing stayed; at 390 the phone menu's Users link → dialog → Leave went to `/admin/users` and the menu closed; Delete document → dialog → Keep it (`flow-knowledge-*.png`). The replace-file dialog is covered by its test only (it needs an edited document; saving text re-indexes it).
- Model Prices at 390: prices as cards, a new long model name fits (`costs-390.png`, `flow-costs-new-model-390.png`).
- Console: no page errors. Before the rebase, only the known `/plan` prefetch 404 (fixed by issue 14); after it, none.

### Tests changed, and why
- `HelplinesManager.test.tsx`, `EvalRunView.test.tsx`, `EvalCostsForm.test.tsx`: queries now look inside the table, because the phone cards repeat each row in the page (markup only).
- `HelplinesManager.test.tsx`, `KnowledgeDocumentView.test.tsx`: confirms now click the dialog's buttons instead of faking `window.confirm` (the behaviour Zaf asked to change).
- New: `lib/use-unsaved-changes-warning.test.ts` (the leave guard holds plain in-app links only).

### Choices I made (please check)
- **Page heads on detail pages** (run, trace, history, Knowledge Document, model-call trace): the back link is the small underlined card link (13px) on top, the title is the admin title (32px cream). No "Admin" eyebrow added where the page didn't use `AdminPageHeader`.
- **Boxes**: every white card became the panel card (`bg-panel`, line border, 16px radius); nested boxes use the 14px tile radius; code and value blocks use `bg-bg-deep` with the 10px input radius.
- **Pills**: run state is cream when Finished, danger when Stopped over limit or Interrupted, outlined otherwise (same as the runs list from issue 11). Outcome: Pass cream, Fail danger, Error outlined (Errors don't count as fails). Knowledge status uses the card tag tones from issue 13 (Ready plain, Pending orange, Failed danger); "Edited" is a plain card tag.
- **States**: loading boxes are `LoadingPanel` (card shape); couldn't-load stays `LoadFailed`; form save results are `SavedNote` / `SaveFailedNote` (Judge, case editor, Model Prices, New Eval Run start error, Knowledge details and replace file); field-level errors stay small danger text under the field. Empty and not-found boxes are dashed boxes in the table-empty look (left aligned, 22px padding), keeping their own words, since `EmptyState` needs a title they don't have.
- **Notes**: "Couldn't be checked" on a result is a danger note; "Made live by…" is a plain note on `bg-bg-deep`; the "changed live since the run started" confirm and "Changed since the run below" line are orange (attention).
- **Grid**: column heads use the table head style; the picked cell is the Zeph colour (`bg-zeph`) with a strong line border; PASS/FAIL check labels are cream/danger.
- **Form fields**: inputs and selects are the card text field look (46px, `bg-bg-deep`, line-strong border, 15px); labels 13px soft; hints 12px soft; field names 15px; section titles 17px cream; native controls use `color-scheme: dark`; checkboxes use cream as the accent; the file picker's button is a small outline pill.
- **Small buttons**: `compactSecondaryButton` is now 44px tall, outline, 13px. The unused `quietButton` was removed.
- **Editor**: toolbar buttons 44px; Edit/Preview/Split is a one-pill toggle (cream when chosen); the toolbar and footer bars look like the form editor's caption bar. CodeMirror: text on transparent (panel), gutter `bg-bg-deep` with mute numbers, active line `bg-bg-deep`, active line number `zeph`, selection `zeph`, cursor cream, search match orange outline (selected match orange fill with ink text), panels and search box `bg-bg-deep`. Markdown: headings cream at weight 400 (no bold), strong cream at 500, links soft underlined, list marks soft.
- **Markdown preview**: h1 24px, h2 20px, h3 17px, h4 15px, all cream weight 400; code and pre on `bg-bg-deep`.
- **Review changes dialog**: the dialog surface from the States sheet; added text on `zeph` in cream; removed text in danger, struck through; backdrop `bg-black/60`.
- **Helplines**: the action column now shows the heading "Actions", as on the other `DataTable` pages; the fallback row lost its darker background (DataTable has no row tint); "Always last" stays soft.
- **Dialog words (new copy)**:
  - Helplines: "Remove <name>?" / "Users in its country stop being shown it. You can add it again later." / Keep it · Remove.
  - Knowledge delete: "Delete <title>?" / "This can't be undone." / Keep it · Delete.
  - Replace file: "Replace your edited text?" / "This document's text was edited. Replacing the file replaces those edits with the new file's text." / Keep my edits · Replace.
  - Discard: "Discard your unsaved text changes?" / "Your edits since the last save aren't kept." / Keep editing · Discard.
  - Leave: "Leave and lose your text changes?" / "Your edits since the last save aren't kept." / Keep editing · Leave.
- **Leave guard**: only plain clicks on in-app links open the dialog. New-tab, middle-click, download, off-site and same-page `#` links go straight to the browser. Reload or closing the tab still uses the browser's own warning (it can't be styled).
- **"Failed:"** on a failed Knowledge document is no longer bold (no bold in the design).

### Open for Zaf
- `OnboardingGate` (User side) still has old-theme classes, and `SettingLabel.tsx` is unused. Neither is an admin page.
- `TableCards` rows are 40px tall (the shared part from issue 10). Buttons inside them are 44px.

## Completion

- Completed: 2026-11-19
- Commit: <filled in after merge>
