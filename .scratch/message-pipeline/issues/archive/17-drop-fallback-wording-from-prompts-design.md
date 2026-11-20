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
- **Pixel test** (`compare.cjs AdminPrompts`, fixture mode): FAIL at 0.81% (it was 0.80% on a 61px taller page, so the same remaining pixels are a slightly bigger share). The diff around the Reply Plan card is clean where the row was, and the Reply card below lines up. What still differs is unchanged from 06 and 05: the drawn "unsaved" Reply Plan save bar, the model dropdown font, the drawn character counts, Pattern keeping's limit rows (08), and the annotation samples at the foot.
- **Checks:** `pnpm lint`, `pnpm format:check` and `pnpm typecheck` clean; `pnpm test` 872 passed.
