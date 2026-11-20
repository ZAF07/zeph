# 17 — Drop the empty "Fallback wording" group from the Prompts design

Status: completed
Lane: A
Blocked by: none

## Parent

`.scratch/message-pipeline/PRD.md`. Found while closing 05 (`.scratch/message-pipeline/issues/archive/05-reply-plan-takes-over-deciding.md`).

## What to build

The `AdminPrompts` design draws a "Fallback wording" group on the Reply Plan card, with no field in it. No setting backs it: when the Reply Plan fails, the reply uses the fallback Need, whose wording Admins already edit on the Needs page. Zaf decided (20 Nov 2026) to drop the heading from the design rather than add a setting.

- Remove the group row from `web/design/reference/AdminPrompts.html` and rebuild `web/design/baseline/AdminPrompts.png` with `node design/shoot.cjs` (on Zaf's machine, where baselines are made).
- Remove it from the design fixture (`web/src/lib/design-fixtures/admin-forms.ts`).

## Acceptance criteria

- [x] `AdminPrompts.html` and its baseline no longer show "Fallback wording"
- [x] The design fixture no longer lists the group
- [x] `node design/compare.cjs AdminPrompts` differs by less than before (0.80%); what still differs is recorded under Comments
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`

## Comments

### Evidence (20 Nov 2026)

- **Design:** the "Fallback wording" row is gone from `AdminPrompts.html`. `node design/shoot.cjs` on Zaf's machine rebuilt the baselines. Only `AdminPrompts.png` changed (3581px to 3520px tall); every other baseline came out byte-identical, so this machine renders them as before.
- **Fixture:** the Reply Plan service in `admin-forms.ts` now has `extra_prompt_groups: []`.
- **Pixel test** (`compare.cjs AdminPrompts`, fixture mode): 0.81% before rebasing. After rebasing on issue 08 (which drew Pattern keeping's limit rows) it is **0.19%**, under the 0.5% limit. It still prints FAIL, only on height (3361 vs 3520px), because the reference ends with annotation samples the app doesn't draw on any template page (see 06). The diff around the Reply Plan card is clean where the row was, and the Reply card below lines up. Pixels that still differ: the drawn "unsaved" Reply Plan save bar, the model dropdown font and the drawn character counts (see 06).
- **Checks:** `pnpm lint`, `pnpm format:check` and `pnpm typecheck` clean; `pnpm test` 873 passed (after the rebase).

## Completion

- Completed: 2026-11-20
- Commits on branch `prompts-drop-fallback-wording`:
  - 9992a0e "Prompts design: drop the empty Fallback wording group from the Reply Plan card (issue 17)"
  - 8e122ba "Issue 17 evidence updated for the rebase on issue 08"
- Merged into main in ad961f0 "Merge issue 17: the Prompts design drops the empty Fallback wording group from the Reply Plan card; the fallback is the fallback Need, edited on the Needs page"
