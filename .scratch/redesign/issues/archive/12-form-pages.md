# 12 — Redesign: form pages (Persona template and the rest)

Status: completed

Lane: A. README slice: 13.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Persona** (`/admin/persona`) to `AdminPersona`. This is the **form template**: the editor, field rows for pages with several settings, and the save bar with all its states (unsaved, saving, saved, couldn't save with Discard and Try again, "Using the starting values"). Build them as reusable parts.
- Then **Prompts & models, Safety, Platform Settings and Features**, from the template's editor or field rows plus its save bar, with each page's real fields. No pixel test for these.
- Same saving, Admin Setting Change captions and unsaved-changes warning as now.
- If a page needs a part the template doesn't have, stop and ask. Fixture data goes in the admin-forms fixture file.

Refs: `AdminPersona`.

## Acceptance criteria

- [x] `AdminPersona` PASSES. (By parts, as Zaf decided: see Evidence.)
- [x] Each of the other four pages uses only form-template parts, with screenshots at both widths attached.
- [x] Each save bar state matches its drawn sample (tested).
- [x] Saving works as before on every page (`/run`).

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

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-19 — Decisions (Zaf, asked at start):
  - AdminPersona: no "Sample data" pill and no orange builder notes or samples (as issues 09/10). Checked by parts: header and editor box pixel-checked against that part of the baseline; each save bar state tested against its drawn values. AdminPersona stays FAIL until its baseline is redrawn.
  - The yellow "honesty rules must stay" note is dropped (not drawn).
  - Features keeps saving each switch as soon as it's flipped: field rows with switches, no save bar. The "Changed … by …" line goes under the description; the visible "On for everyone" text is dropped (the switch keeps its label); a failed flip uses the shared error note.
  - Undrawn parts: build from the nearest template parts and list every choice here. Prompts: per service a field-rows box (Model select, Thinking switch), prompt and extra prompts as editors, one save bar per service; folded groups use the card-list chevron. Platform settings: a field-rows box per section with a small heading, number inputs in the drawn value box plus unit, wording as editors, one save bar. Safety: Crisis Reply = editor + save bar; Helplines keep their table, reskinned with tokens only.

- 2026-11-19 — Evidence (branch `redesign-12-form-pages`, rebased on `origin/main` at `2fd47ce`; main had not moved).

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3020`, `BASE_URL=http://localhost:3020`, sessions from `design-sessions.sh`):
```
FAIL  AdminPersona                       1.10% differs, height 800 vs 1672
PASS  Dashboard                          0.01% differs, height 1268 vs 1268
PASS  Dashboard--menu-folded             0.00% differs, height 1268 vs 1268
PASS  Account                            0.03% differs, height 1503 vs 1503
```
AdminPersona fails only on what Zaf chose to leave out (the "Sample data" pill, the builder notes and their samples, 872px). Checked by parts, with the same pixelmatch settings. The editor was given one trailing space so the bar shows the drawn "Unsaved changes" state:
```
AdminPersona top 584px (header, editor, save bar): 0.05% differs
```
That 0.05% is the "Sample data" pill, the character count and the textarea's resize grip. The reference's text is 267 characters, though it prints "312 characters". The app shows the real count.

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 100 files, 627 tests passed.

**Save bar states (tested)**: `SaveBar.test.tsx` covers:
- nothing changed: the note, plus both buttons off in the drawn off look;
- unsaved: the orange tag (border, padding, 12px), the outline Discard and the cream Save;
- saving: tag shown, both buttons off, "Saving…";
- save failed: the coral alert, Discard on, "Try again" saves;
- Save off while the edit can't be saved;
- the bar on its own panel, and at the foot of a box.

`FieldRows.test.tsx` covers the field row box, rows and "Using the starting values" footnote.

**/run with real data** (worktree stack, production web container, real Admin session). Screenshots are in `12-screenshots/` beside this file: both widths for each page. The Prompts shots are the top 3000px of 17016px and 28167px pages.
- Every form page at 390 is 390 wide (no sideways scroll).
  - Two overflows were found and fixed: the long "runs when" pill on Prompts, and the hidden "Actions" table heading on Safety.
  - Long values wrap: the long run-check test email in Features' "Changed … by …" line, and long Helpline names on a phone.
- Persona: an edit showed "Unsaved changes" → Save → "Saved. Zeph uses it from the next message." and "Last saved 19 Nov 2026, 10:19 AM by Run check". The text was restored.
  - With the backend stopped, Save showed "Couldn’t save. Your text is still here." and kept the text.
  - After a restart, Try again saved on the 2nd press (the 1st came while the backend was still waking up).
- Prompts: Thinking off → Save → "Saved." (true → false), then switched back.
- Safety: Crisis Reply edited, saved and restored. Add Helpline opens the field-row form; Cancel closes it.
- Platform settings: Daily message limit 200 → 201 saved, then back to 200.
- Features: Web Search off for everyone (saved instantly), then back on.
- No page errors anywhere.

**Chosen myself / unsure (for Zaf to confirm).**
- Admin layout: `admin/layout.tsx` drops the old `max-w-[1120px] gap-8 text-sm` column for all admin pages, since the references draw pages straight in `<main>`. Issue 10 makes the same change, and `AdminPageHeader` is copied from issue 10's version so the two merge cleanly.
- The Persona editor is a textarea, not a `pre`. It grows with its text (`field-sizing: content`), with the drawn 300px as the least height. Extra prompts, Crisis Reply and wording boxes use a short 120px least height.
- Last saved lines use the drawn format "12 Nov 2026, 9:14 PM" (new `formatLastSavedAt`). They used to read "12 Nov, 21:14".
- Wording:
  - Each page keeps its own save-failed words in the bar; only Persona uses the drawn "Couldn’t save. Your text is still here.". Backend 422 reasons still show.
  - Prompts, Crisis Reply and Platform settings say "Saved." in the shared note.
  - The bar's "Changes apply to the next message after saving." is the template's fixed line on every page, Platform settings included.
- Discard is new on Prompts and Crisis Reply (it comes with the template's save bar).
- Section headings (Crisis Reply, Helplines, each service, each Platform settings section) use the field row's title and caption type (15px / 13px).
- Prompts:
  - one part per service: heading with the "runs when" pill (allowed to wrap), field rows for Model and Thinking, the Prompt editor (last saved line on top), extra prompts as short editors (name · hint on top), and one save bar per service;
  - folded groups are `<details>` with the select's chevron turned right, 150ms;
  - services are 24px apart, in one column (they were in two).
- Platform settings: a field-row box per section, each with its own "Last saved / Using the starting values" footnote. Number boxes put the unit inside, at the end. Wording is 14 short editors, with the section's last saved line under the "Wording" heading. One sticky save bar (no shadow).
- Helplines:
  - the table is reskinned with tokens: 11px / 1.5px uppercase heads, panel box, deep-blue fallback row, 44px round arrow and remove buttons, outline Edit;
  - empty state uses the shared `EmptyState`, messages use `SavedNote` / `SaveFailedNote`;
  - the add/edit form uses field rows (Country select, Name, Number, Hours) with no new copy;
  - **Not as the README says**: on a phone the table still scrolls sideways inside its box, as before. The README wants rows to become cards; that part is the table template (issue 10, not merged yet).
- Features: field rows; "Changed … by …" is a 12px line under the description.
- Loading states use the shared `LoadingPanel`.

**Existing tests changed.**
- `PersonaEditor.test.tsx`: the honesty note check is gone (note dropped). The failure test checks the bar's alert text and that Try again saves.
- `CrisisReplyEditor.test.tsx` and `PlatformSettingsForm.test.tsx`: "Saved" is now "Saved." (shared note). There are several "Using the starting values" lines now (one per section). The Platform settings failure test reads the bar's alert.
- `PromptsAndModels.test.tsx`: the failure test reads the bar's alert and checks for "Try again".
- `AdminFeatures.test.tsx`: no logic change (rows are still `li`).
- `settings.test.ts`: new date format.

**Code review** (two sub-agents, standards and spec).
- Fixed:
  - each page keeps its own save-failed and saved words (spec: "same saving as now");
  - one `ChevronDownIcon` instead of two copies;
  - `describedById` used in both places;
  - an unexplained alias removed;
  - the Saving test also checks the drawn off colours;
  - new `FieldRows` test.
- Answered, not changed:
  - `SaveBar` takes plain props rather than the save mutation, so it stays free of the data library and easy to test;
  - the repeated "set draft + reset save" handlers are one line each and read clearly where they are;
  - the admin layout, date format, Helpline form and phone table are listed above for Zaf.

## Completion

- Completed: 2026-11-19
- Commit: merge `1259f27` into main — "Merge redesign issue 12: form pages — Persona as the form template (editor, field rows, save bar with its four states) and Prompts & models, Safety, Platform settings and Features built from its parts; saving works as before, each page keeps its own words; Helplines table reskinned with tokens"
  - Branch `redesign-12-form-pages`:
    - `cb65ace` Redesign 12: form pages in the new look — Persona (form template: editor, field rows, save bar) and Prompts & models, Safety, Platform settings and Features from its parts
    - `58d3717` Redesign 12: code-review fixes — pages keep their own save-failed and saved wording, one chevron icon, describedById, more save bar and field row tests
    - `11af4e9` Redesign 12: evidence recorded, issue completed and archived, screenshots at both widths
