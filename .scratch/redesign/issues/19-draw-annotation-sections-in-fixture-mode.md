# 19 — Draw the annotation sections in fixture mode

Status: needs-triage

## Parent

`.scratch/redesign/PRD.md` (found while closing `.scratch/message-pipeline/issues/archive/14-patterns-in-replies.md`)

## What to build

`web/design/README.md` says: "The annotation rows and the samples under them are rendered in fixture mode, as on the other template pages." No page does this yet. Every reference with an orange dashed annotation section fails the pixel test on height alone, even where everything above the dashed line lines up. On 20 Nov 2026 these were: `AdminModelCallTrace` (0.02%, 1357 vs 2274), `AdminCheckInKinds`, `AdminCheckInKinds--all-folded`, `AdminCheckInLog`, `M-AdminCheckInLog`, `M-AdminCheckInKinds`, `AdminPersona`, `AdminPrompts`, `ConnectTelegram`, `M-ConnectTelegram`.

Decide how to draw them, then do it page by page:

- Some samples show a state the real part can be put in (e.g. "Other states of this table": empty, loading, error). These could render the real component with fixture data.
- Some samples differ from what the app really draws. On `AdminModelCallTrace`:
  - "Content, opened" uses 13px headings, bordered 13px blocks, one block per tool call and no History section, while `ModelCallContentDetails` differs.
  - "For a User who is not an Admin" lists only Need picked, Read formed, Read said and Pattern, while the real card lists every fact.

  Either the real part changes to match, or the sample is drawn by a fixture-only block. Zaf to decide.

## Acceptance criteria

- [ ] A decision on real component vs fixture-only sample, recorded here
- [ ] Each listed page's annotation section renders in fixture mode, and `node design/compare.cjs <Ref>` prints PASS (or the leftover parts are recorded with an owner)
- [ ] Nothing extra shows outside fixture mode
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`

## Comments

- 24 Nov 2026: still failing on height on `main`: `AdminCheckInKinds` (0.08%, 1147 vs 2270), `AdminCheckInKinds--all-folded` (0.14%, 800 vs 1915), `AdminCheckInLog` (0.11%, 837 vs 1470), `AdminModelCallTrace` (0.02%, 1357 vs 2274), `AdminPersona` (0.71%, 800 vs 1968). `AdminPrompts` passed this time. `AdminUsers` also fails but has no annotation section; filed as issue 21.
