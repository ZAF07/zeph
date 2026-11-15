# 04 — Cases lane: Admins edit Eval Cases and the Judge on the Dashboard

Status: completed

## Parent

`.scratch/eval-dashboard/PRD.md`

## What to build

Lane B (case and Judge pages). Runs in parallel with 03.

- **Eval Cases are Admin-managed (ADR-0004):** a list per Eval; add, edit, duplicate, archive. Archived cases stay so old runs still show them, and can't be picked for a new run.
- **One form style for every Eval** (no YAML). Each Eval has a typed case shape that checks a save and drives its form. Every field has a plain description of what it means and what changing it affects (e.g. "Expected Need — the Need the Companion should pick for this Message; the case fails if it picks another"). Understanding, Persona and Knowledge cases are split into sections (made-up User Memory, earlier messages, Messages and what to expect). A save that doesn't fit the shape says clearly what's wrong.
- **Photo cases** upload their images, kept with the case.
- **Seed rule:** the seed adds only keys not in the database; it never overwrites an edited case or brings back an archived one. Dashboard edits don't go back to the files.
- **Judge settings:** the Judge's model, thinking (once issue 22 lands) and prompts become Admin-managed, seeded from a file, edited in the Eval area in the same form style. Runs already keep the Judge settings they used (from 02).

## Acceptance criteria

- [x] An Admin can add, edit, duplicate and archive cases for all six Evals in forms, with a description on every field (`tests/test_eval_cases.py::test_an_admin_adds_edits_duplicates_and_archives_a_case_of_every_eval` for all six; `test_every_field_of_every_case_shape_and_the_judge_has_a_description`; `/run`: added a Photo descriptions case, edited, duplicated and archived Persona cases in the browser)
- [x] An invalid save is refused with a clear message per field (422 with `fields` by path: `test_an_invalid_save_is_refused_with_a_message_per_field`, `test_an_eval_s_own_checks_point_at_the_field_that_is_wrong`; `/run`: a duplicate rule ID showed "Used twice; each rule needs its own." under the field, a taken copy key showed "Another case has this key.")
- [x] Photo cases take uploaded images and the runner uses them (`test_a_photo_case_sends_the_image_uploaded_for_it`: the photo viewer gets the uploaded bytes; `/run`: uploaded house-drawing.png, previewed and saved as `house-drawing-39d1d234.png` in `eval_images`)
- [x] An edited case is used by the next run; old runs still show the case as it was (`test_an_edited_case_and_judge_are_used_by_the_next_run_and_old_runs_keep_theirs`: the reply sees the new text, the old run's snapshot and Case Result keep the old content)
- [x] The seed adds new keys only; edited and archived cases are left alone (test) (`test_the_seed_leaves_a_case_edited_on_the_dashboard_and_an_archived_one_alone`, `test_the_seed_adds_only_new_keys_and_never_overwrites_or_restores`; `/run`: a backend restart re-seeded and kept the edit, the archive and the Judge change)
- [x] Judge model and prompts are edited on the Dashboard and used by the next run (`test_an_admin_edits_the_judge_and_a_model_not_listed_is_refused`; the runner test above checks the Judge call used the new thinking and prompt; `/run`: turned Thinking on and saved; `eval_judge_settings.thinking = true`)
- [x] Tests at the API, at "work the next Queued run" (an edited case and edited Judge are used), and Dashboard component tests (`tests/test_eval_cases.py` 29; `tests/test_eval_runner.py` 3 new; `EvalCaseForm.test.tsx`, `EvalCasesList.test.tsx`, `JudgeSettingsForm.test.tsx`)
- [x] Verified at `/run`; `make check-python` and `make check-web` pass (1031 Python tests, ruff, ruff format, mypy; 394 web tests, eslint, prettier, tsc)

## Parallel work

03 runs at the same time. Pages, core modules and tables don't overlap. Both add a migration and touch the API client and admin nav: whoever rebases second renumbers their migration's parent and keeps both sides' entries.

## Blocked by

- `02-eval-runs-from-the-dashboard.md`

## Comments

- 2026-11-15 (implementing, branch `eval-dashboard-04-edit-cases-judge`): plan.
  - **Case shapes in core** (`core/evals/case_shapes.py`): each Eval's case shape is a list of sections of described fields (text, long text, whole number, on/off, choice, date and time, image, list of text, group, list of groups). The same shape checks a save (a message per field path, e.g. `messages.0.text`) and is sent to the Dashboard to draw the form, so the form has no rules of its own. The Eval's own cross checks (Thread titles, forgotten Memory Items) run after it.
  - **Regular content:** content becomes plain fields the form can write: Persona messages always `{text, photo, shows}`, rules and Memory Items lists of `{id, check}` / `{category, contents}`, earlier lines `{who, text}`. The seed reader writes this shape; the migration rewrites stored cases once (run snapshots are left as they were).
  - **Images** live in a new `eval_images` table (name, bytes, type). The seed adds its images there; uploads get a fresh name so a stored image never changes and old runs still point at what they used. The runner hands each case its images; nothing reads the images folder at run time.
  - **Judge settings:** a new `eval_judge_settings` table seeded from `seed/evals/judge.yaml` (add missing keys only), not Platform Settings, so Setting Overrides can never change the Judge. The runner reads them at run start, snapshots them and passes them to the Persona, Knowledge and Understanding checks. Model must be one of the Available models.
  - **API:** new `eval_case_api.py` (keeps clear of 03's `eval_api.py`): shapes, list/get/add/edit/duplicate/archive cases, image upload/download, Judge get/save. A case save that doesn't fit answers 422 with `fields` (path → message) beside `detail`.
  - **Dashboard:** Runs / Cases / Judge tabs in the Eval area; cases list per Eval; one shape-driven case form; Judge form in the same style.
  - Migration 0043 (03 also adds one; whoever rebases second renumbers).
- 2026-11-15 (done): built as planned, reviewed and verified.
  - `/run` in the worktree stack with a copy of the main database (`make db-copy`): migration 0043 rewrote the 70 stored cases and all 70 fit their shapes and Eval checks; 4 seed images and the 4 Judge settings were seeded. In the browser: Cases list per Eval, the Understanding case in its four sections, a Safeguard photo case at 390 px, a new Photo descriptions case with an uploaded image, a refused Persona save with the message under the field, an edit ("Saved. The next run uses it"), duplicate (taken key refused, then opened the copy), archive, and Judge Thinking on. A backend restart (re-seed) kept every change. No page errors.
  - Not done: a real `make eval` / Dashboard run. It costs money and this slice keeps every case's content and the Judge's prompts as they were, so the Companion's behaviour is unchanged; the runner path is covered with the scripted model. Worth one run before the next prompt change.
  - `/code-review`: no standards violations; fixed a run that would stay Running if a Judge setting were missing (now each case is an Error and the run finishes; test added), shared `InvalidFormError` for case and Judge forms, named `archived` flag, one refusal helper, one image-name helper, one cache-refresh helper. Left as judgement calls: the six shapes and the checker share `case_shapes.py`; the per-kind branches stay in plain `if`s.
  - Notes for 03 (run pages, history, Re-run failed): run snapshots and Case Results from before 0043 keep the old case shape (rules as a mapping, Persona messages as text, earlier lines as `{person|zeph}`) and the Judge snapshot's `thinking` as "on"/"off". Show snapshots as stored; don't read them through `read_case` or `JudgeSettings.from_values`. Re-run failed reads the live cases, so it's unaffected.
  - Known limits: an uploaded image that is never saved in a case stays in `eval_images`; removing the Judge's model from Available models doesn't warn (the Judge keeps it until saved again); an archived case can be duplicated into a live copy (on purpose, the form says so).

## Completion

- Completed: 2026-11-15
- Commits (branch `eval-dashboard-04-edit-cases-judge`):
  - `700c8b8` Eval dashboard issue 04: Admins edit Eval Cases and the Judge
  - `c939582` Eval dashboard issue 04: on/off fields don't say optional
  - `1d63a1f` Eval dashboard issue 04: review fixes
  - `0a96749` Eval dashboard issue 04: CONTEXT.md and ADRs 0014-0015 for case shapes and the Judge's own settings
  - `9cb852c` Eval dashboard issue 04: evals README on editing cases and the Judge
- Archive commit: `b96e525` Eval dashboard issue 04 done: archive issue with run, review and check evidence
  - `a9112c5` Eval dashboard issue 04: list the docs commits in the archived issue
- Merge commit: `959a487` Merge eval dashboard issue 04 into main
