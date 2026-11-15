# 04 — Cases lane: Admins edit Eval Cases and the Judge on the Dashboard

Status: ready-for-agent

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

- [ ] An Admin can add, edit, duplicate and archive cases for all six Evals in forms, with a description on every field
- [ ] An invalid save is refused with a clear message per field
- [ ] Photo cases take uploaded images and the runner uses them
- [ ] An edited case is used by the next run; old runs still show the case as it was
- [ ] The seed adds new keys only; edited and archived cases are left alone (test)
- [ ] Judge model and prompts are edited on the Dashboard and used by the next run
- [ ] Tests at the API, at "work the next Queued run" (an edited case and edited Judge are used), and Dashboard component tests
- [ ] Verified at `/run`; `make check-python` and `make check-web` pass

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
