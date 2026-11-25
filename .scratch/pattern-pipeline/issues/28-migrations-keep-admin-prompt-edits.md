# 28 — A migration that reloads a prompt keeps an Admin's edits

Status: ready-for-agent
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (sections 02, 03, 08 and 09), triaged with the owner on 25 Nov 2026 as high risk.

## Why

Migrations 0073, 0078, 0080, 0081, 0086, 0100 and 0101 each drop a stored prompt so it reloads from the seed. If an Admin edited that prompt on the Dashboard, the edit is lost on deploy and nothing says so. Production is live, and every later prompt change will do the same.

## What to build

One shared helper that later migrations call to reload a prompt:

- It drops the stored prompt only when the stored text still equals the seed text it replaces (the Admin never edited it).
- When the stored text differs, it keeps the Admin's text and logs a warning naming the setting, so the owner knows to merge the new seed text by hand.
- The migration passes the previous seed text (or its hash) itself, so the helper doesn't depend on the seed file as it is today.

Also:

- A short note in the migrations guide (or wherever migrations are described) saying new migrations must use the helper.
- Don't rewrite the old migrations; they have already run on prod.
- Say in Comments which stored prompts on prod differ from today's seed, if the owner wants to know what was already lost. Ask before touching prod.

Design for many Users and more than one backend: the helper runs inside the migration, with no in-process state.

## Acceptance criteria

- [ ] A helper reloads a stored prompt only when it equals the previous seed text
- [ ] An edited prompt is kept and a warning naming the setting is logged
- [ ] Tests cover both: unedited prompt reloads, edited prompt stays
- [ ] The guide says new migrations use the helper
- [ ] Checked in the running app (`/run`): edit a prompt on the Dashboard, run a migration that uses the helper, the edit is still there and the warning is in the log
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass

## Where to start

- `src/companion/adapters/postgres/migrations/versions/0100_pattern_sharing.py` and `0101_prediction_follow_up.py` for how prompts are dropped today.
- Seed prompts: `src/companion/seed/platform_settings.yaml`.

## Comments
