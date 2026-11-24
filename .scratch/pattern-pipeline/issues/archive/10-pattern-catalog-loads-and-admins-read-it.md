# 10 — The Pattern Catalog loads from YAML and Admins can read it

Status: completed
Track: B
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 64, 65, 67). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Pattern Types live in the repo as YAML and are loaded into the database on deploy (ADR-0025). Each has a stable ID, a version, one of five areas (conflict, approval, control, achievement, relationships), a definition, its if / then / function, signs (each with a strength and the part it shows), signs against, look-alikes with what tells them apart (including what anyone would do), exclusions (each saying whether evidence is ignored or counted but not shared), approved wording, Prediction wording, its own numbers, and a status (draft, approved with who and when, or archived).

The loader refuses a malformed Pattern Type and says why. Past versions are kept. Admins read every Pattern Type on a new read-only Dashboard page. This issue ships the three already drafted in the source catalog doc (linked from `.scratch/pattern-pipeline/grill-decisions.md`), all as draft.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] The three drafted Pattern Types are YAML in the repo and load into the database when the backend starts
- [x] A Pattern Type missing a required field, naming an unknown look-alike or using a value outside a fixed list stops the load with a clear message
- [x] Changing a Pattern Type's version keeps the old version's row
- [x] Admins see each Pattern Type with all its details and status on the Dashboard, with no way to edit
- [x] A non-Admin can't reach the page or its API
- [x] Nothing in the reply path changes yet
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments

Decisions made while building (24 Nov 2026, branch `pattern-10-pattern-catalog`):

- **Files.** One YAML file per Pattern Type in `src/companion/seed/pattern_catalog/`. Fields: `id`, `version`, `area`, `name`, `status` (with `approved_by` and `approved_on` once approved), `definition`, `if` / `then` / `function`, `frameworks`, `signs`, `signs_against` (each with `id`, `text`, `strength`, `part`), `look_alikes` (a `pattern_type` ID or a `name`, plus `tells_apart`), `anyone_would`, `exclusions` (`text`, `evidence`: `ignored` or `counted_not_shared`), `approved_wording`, `prediction_wording`, `numbers` (`situations_needed`, `base_rate`).
- **A sign's part** is `situation`, `inside` or `behaviour`, as `CONTEXT.md` words it, not the source doc's five CAPS units. The source doc gave no part per sign, so the parts on the three Pattern Types are first drafts for the owner to check. So is `anyone_would` on ACH.WORTH.PERF, which the source doc did not have.
- **Versions.** A row is one (ID, version) and never changes. A change that keeps its version is refused. Going back to an earlier version makes that row current again. A Pattern Type whose file is removed leaves the catalog; its rows stay.
- **A bad catalog does not stop the backend.** The load is all or nothing. On a failure the problems are printed in the start log and the backend starts on the catalog as it was last loaded, so a bad file can't stop Zeph replying to real Users. The first build stopped the start instead; changed after review. The cost: a refused change is only seen in the start log or as an unchanged version on the page.
- **Thought Experiments** (the source doc's probes) are left out of the files: issue 05 makes them Admin data. The Admin guide is issue 15's.
- **Design files.** `web/design/README.md` says agents never edit `reference/`, `baseline/`, `routes.json` or `manifest.json`; this issue says to add the reference, so the issue was followed, as admin-ui issue 01 did. Added `AdminPatternCatalog.html` (built only from card-list template parts), its baseline, and its lines in `routes.json` and `manifest.json`. The new "Pattern Catalog" menu link was added to the ten other admin reference pages and their baselines reshot; `shoot.cjs` was first run on the untouched references and changed no baseline, so the only pixel changes are the menu link. No phone reference: checked by eye at 390.

Evidence (24 Nov 2026, worktree stack on ports 3020/8020, real data, final build):

- **Three Pattern Types load on start.** After `make restart` on an empty table, `pattern_types` held ACH.WORTH.PERF, CONF.AVOID.BELONG and CTRL.UNCERT.PLAN, each `0.1.0`, current, `draft`. Tests: `test_the_three_drafted_pattern_types_are_loaded_on_start`, `test_the_three_drafted_pattern_types_in_the_repo_are_valid_drafts`.
- **Malformed stops the load with a clear message.** A file with `if` removed, a sign strength of `huge` and look-alike `ACH.NOT.THERE` was copied into the running backend and it was restarted. Start log: "The Pattern Catalog can't be loaded. Nothing was changed. / - conf-avoid-belong.yaml: if is missing. / - conf-avoid-belong.yaml: signs[1].strength is huge; it must be one of weak, moderate, strong. / - conf-avoid-belong.yaml: look_alikes[1].pattern_type is ACH.NOT.THERE, which is not a Pattern Type in the catalog. / The backend starts with the catalog as it was last loaded." `/health` 200 and the three rows unchanged. Tests: 33 cases in `tests/test_pattern_catalog_reader.py`, `test_a_malformed_pattern_type_stops_the_whole_load`, `test_on_start_a_catalog_that_cannot_be_loaded_is_reported_and_the_last_kept`.
- **A new version keeps the old row.** The same file with `version: 0.2.0` and a new name, restarted: rows `CONF.AVOID.BELONG 0.1.0 current=f` (old name) and `0.2.0 current=t` (new name); the page showed "v0.2.0" and "Also kept 0.1.0". A further change kept at `0.2.0` was refused: "CONF.AVOID.BELONG has changed but its version is still 0.2.0. Give it a new version; a stored version never changes." Tests: `test_a_new_version_becomes_current_and_the_old_version_row_is_kept`, `test_a_change_under_a_version_already_stored_is_refused`.
- **Admins see every detail, with no way to edit.** Signed-in Admin on `/admin/pattern-catalog`, 1280 and 390: three cards, first open, 3 open after Expand all, 0 after Collapse all; each card has What it is, Signs, Signs against, Look-alikes, Exclusions, Wording, Numbers and status; 0 inputs, selects, switches or text areas; the only buttons are Expand all, Collapse all and the three card rows; no sideways scroll; no page errors. With the Admin's own token the API answered PUT, POST and DELETE with 405 and a PUT on one Pattern Type with 404. Pixel test: `PASS AdminPatternCatalog 0.00% differs, height 2514 vs 2514`. Tests: `PatternCatalog.test.tsx` (7), `test_admin_reads_a_pattern_type_with_all_its_details`, `test_the_pattern_catalog_cannot_be_changed_through_the_api`.
- **A non-Admin can't reach the page or its API.** Signed-in plain User: `/admin/pattern-catalog` sent them to Home, no menu link, and the API answered 403 to their token; signed out it answered 401. Tests: `test_a_plain_user_cannot_read_the_pattern_catalog`, `test_a_signed_out_visitor_cannot_read_the_pattern_catalog`.
- **Nothing in the reply path changes.** The branch touches no reply, Reply Plan, Understanding or Conversation-end file: backend changes are the new catalog modules, the new table and repository, one router in `app.py`, the load in `prestart.py`, and additions to `models.py` and `ports.py`. All 1720 backend tests pass unchanged. In the running stack a Telegram update posted to `/telegram/webhook` was accepted (200) and went through the reply gate as before, up to Telegram refusing the made-up chat ID, the known worktree limit; a real reply was not sent from the worktree.
- **Checks.** `make check`: ruff clean, ruff format clean, mypy clean (229 files), pytest 1720 passed; `pnpm lint`, `pnpm format:check` and `pnpm typecheck` clean, `pnpm test` 135 files, 919 tests passed.
- **Pixel test notes.** Run with a git-ignored copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes, which never finish on this machine; nothing else changed. Admin, AdminPrompts, AdminPersonaOutlook, AdminEvalDaySummaryCase and AdminPatternCatalog pass. AdminUsers, AdminCheckInLog, AdminPersona, AdminModelCallTrace, AdminCheckInKinds and its all-folded state fail on page height; they fail the same way, with the same numbers, on `main` without this branch.
- **Review.** Standards and spec reviews run. Fixed: the bad-catalog start (above), `anyone_would` now required, approval fields go together, a look-alike `name` that looks like an ID is refused, the look-alike's Pattern Type name is filled in by the catalog service not the API, clearer names. Left: the empty and couldn't-load wording on the page is not drawn in the reference (the shared `EmptyState` and `LoadFailed` parts are used, as on other admin pages); a stored version is checked again when read, so if the rules get stricter and a file is not given a new version, the page shows "Couldn't load" until it is.

## Completion

- Completed: 2026-11-24
- Commit: <filled in after the merge>
