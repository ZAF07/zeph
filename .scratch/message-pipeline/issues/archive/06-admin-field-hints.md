# 06 — Every Admin field explains itself

Status: completed
Lane: B
Blocked by: 04

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Every editable setting on the settings page (the Persona, each prompt, model, thinking switch, limit and wording), and every field on the Needs, Moves and Check-in Kinds pages, shows a short hint under its label: what it is, what it serves, and which step reads it and when. One or two sentences, not a manual. Example (for the Outlook, which arrives in 07): "How Zeph sees people and what helps them grow. Zeph forms its Read of each User from this before every reply. Plain prose."

The `hint` mechanism exists today but 64 of 76 settings have none. Hints describe the pipeline in `docs/message-pipeline/README.md` as it stands when this lands; settings added later by other issues bring their own hints. Admin page words that aren't Copy stay in code (ADR-0019).

User stories covered: 61.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- Every editable field has a hint under its label: 13px, soft, at most two sentences. An editor (prompt, Persona text) gets a label and hint above it.
- References: `AdminPrompts` (hint under Model, Thinking and every limit; a Prompt label and hint above each editor), `AdminPersona`, `AdminCheckInKinds`. Do not restyle anything else on a service card.
- Needs and Moves have no reference file: use the same hint style as `AdminCheckInKinds`.
- **Shared references.** `AdminPrompts` also draws 05, 08 and 09; `AdminPersona` also draws 07's tabs. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminCheckInKinds` is yours alone.

## Acceptance criteria

- [x] Every editable setting returned by the Admin settings API has a non-empty hint
- [x] The Needs, Moves and Check-in Kinds admin pages show a hint under each field
- [x] Hints are at most two sentences and name the step that reads the setting
- [x] A test fails if a new editable setting is added without a hint
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] `node design/compare.cjs AdminCheckInKinds` prints PASS (both widths, and `--all-folded`)
- [x] Hints on `AdminPrompts` and `AdminPersona` match the reference (`node design/compare.cjs AdminPrompts AdminPersona`); full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 04 — Commitments followed up, goals kept, one home per thing learned (`.scratch/message-pipeline/issues/04-commitments-goals-one-home.md`)

## Comments

### 2026-11-20 — evidence

- **Every editable setting has a hint:** `hint: str` is now a required field on `EditableSetting` (`src/companion/core/platform_settings.py`), so a setting without one can't be built. `test_every_editable_setting_comes_with_a_short_hint` checks the settings API returns every editable setting with a non-empty hint of at most two sentences. In the running worktree stack, the Admin settings API returned 87 settings and none were missing a hint. The issue counted 76; more settings have been added since.
- **Needs, Moves, Check-in Kinds:** every field on Needs and Moves has a hint naming the step. Tests: `NeedsManager.test.tsx` and `MovesManager.test.tsx` "says under each field what it is for and which step reads it". Check-in Kinds already showed a hint under both fields, drawn in its pixel-tested reference, so it is unchanged. Screenshots of `/admin/needs` and `/admin/moves` in the running app show the hints under each field.
- **Two sentences, names the step:** enforced by the API test for length. After the spec review, six wording and limit hints were rewritten to name their step (Message Retention clean-up, Settings in Chat, Check-ins scheduler, Telegram connection step, Delete My Data, the Reply's typing). Following the design (`web/design/reference/AdminPrompts.html`), every model uses the same hint and so does every thinking switch, shown under the step's heading: "Which model this step calls…" and "Lets the model reason…".
- **UI follows the design** (`web/design/README.md`, "Message-pipeline additions", issue 06): the hint sits under each field's name (13px, soft). Each editor (the Persona, each prompt, extra prompt and wording) has its name and hint above it, via the new `EditorLabel`. The Crisis Reply shows its API hint under its heading. A hover "i" was tried first and dropped, because the design draws the hints in plain view.
- **Pixel test** (`compare.cjs` with the design fixtures, after rebasing on `0a70275 updated designs`): AdminPrompts differs by 0.80%. Every part this issue changed lines up exactly in all four drawn sections: the Model and Thinking hints, and the Prompt label and hint. What still differs belongs elsewhere:
  - Pattern keeping's two limit rows (issue 08)
  - the drawn "unsaved" Reply Plan save bar
  - the drawn character counts, which don't match the drawn texts
  - the model dropdown font, which is monospace in the drawing and was already different before this issue
  - the footer note

  AdminPersona's label and hint block has the drawn shape, offset by the Voice/Outlook tabs (issue 07). Note for later: every template page, including untouched ones (Check-in log, Users), ends at the dashed "other states" line, because the app doesn't draw the annotation samples. Their baselines were the same height before this issue.
- **Docs:** the hints section of `docs/message-pipeline/README.md` now has a "Built" note in place of the "Today" note. In `CONTEXT.md`, Platform Settings now says each setting carries a hint.
- **Checks:** `uv run pytest`: 1359 passed. `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy src`: clean. `pnpm lint`, `pnpm format:check` and `pnpm typecheck`: clean. `pnpm test`: 871 passed. One run had a load timeout in `UserFeatureSwitches.test.tsx`, which is unrelated; it passed on its own and in the next full run.
- **Running app (`/run`, worktree stack on port 3020):** looked at `/admin/persona`, `/admin/prompts` (1280 and 390), `/admin/settings`, `/admin/safety`, `/admin/needs`, `/admin/moves` and `/admin/check-in-kinds`, signed in as Admin. Every field showed its hint, with no page errors.
- **Code review:** standards and spec reviews ran. Fixed from them:
  - the model and thinking hints are now shared constants
  - the helper is renamed to `hintFor`, and `settingKeyFor` is shared
  - each hint id is built once
  - the unused `label` field is dropped from the settings API
  - the Safeguard hint no longer says "before anything else" (photo viewing comes first)
  - the Curiosities limit hint is fixed
  - the Crisis Reply now shows its hint
  - the README note is rewritten to match what was built

  Left as is: the Thinking switch's screen-reader label is now "Thinking for <service>", as the design draws it.

## Completion

- Completed: 2026-11-20
- Commit: 4ac8e8a — Merge message pipeline issue 06: every Admin field explains itself; each editable setting has a required hint (what it is, what it serves, which step reads it) sent by the settings API and shown under each field's name, with editors getting their name and hint above them as drawn; Needs and Moves hints name the step; Crisis Reply shows its hint; Prompts & models design fixture
- Branch commits: 51b02ff (hints), 474b523 (review fixes), 2b01cb1 (Prompts fixture), f6ba78e (evidence and archive)
