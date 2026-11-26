# 28 — A migration that reloads a prompt keeps an Admin's edits

Status: completed
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

- [x] A helper reloads a stored prompt only when it equals the previous seed text
- [x] An edited prompt is kept and a warning naming the setting is logged
- [x] Tests cover both: unedited prompt reloads, edited prompt stays
- [x] The guide says new migrations use the helper
- [x] Checked in the running app (`/run`): edit a prompt on the Dashboard, run a migration that uses the helper, the edit is still there and the warning is in the log
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass

## Where to start

- `src/companion/adapters/postgres/migrations/versions/0100_pattern_sharing.py` and `0101_prediction_follow_up.py` for how prompts are dropped today.
- Seed prompts: `src/companion/seed/platform_settings.yaml`.

## Comments

### 25 Nov 2026: built and checked

**What was built**

- `reload_prompt_unless_edited(connection, key, previous_seed_hash)` in `src/companion/adapters/postgres/prompt_reload.py`. One `DELETE` removes the stored prompt only where the SHA-256 of its text equals the hash the migration passes. If the prompt is still stored after that, it logs a warning naming the setting. A prompt that isn't stored is left alone. A hash that isn't a full 64-character hash is refused, so a typo can't pass for an Admin's edit. No in-process state.
- `uv run python -m scripts.seed_prompt_hash <setting key> [git ref]` prints the hash of a seed prompt as it is on `main` (or another ref), for writing into the migration.
- The guide: `src/companion/adapters/postgres/migrations/README.md`, with a one-line pointer in `CLAUDE.md` (a shared file) so agents find it. ADR 0029 records the decision.
- No old migration was changed.

**Evidence per criterion**

- **Reloads only when it equals the previous seed.** `test_a_prompt_still_at_the_previous_seed_reloads_from_the_new_seed` (the row is removed, then the seed loads the new text); `test_a_prompt_not_stored_yet_is_left_alone_without_a_warning`.
- **An edited prompt is kept and a warning names the setting.** `test_a_prompt_an_admin_edited_is_kept_and_a_warning_names_it`.
- **Tests cover both.** `tests/test_prompt_reload.py`, 6 tests, all pass.
- **The guide says new migrations use the helper.** The migrations README, section "Changing a seed prompt".
- **Checked in the running app.** In this worktree's own stack (commit 9682fcfe): signed in as an Admin, added "ADMIN EDIT FOR ISSUE 28: keep me." to the Safeguard prompt on Prompts & models and saved (1680 → 1715 characters in `platform_settings`). Added a throwaway migration 0102 that calls the helper for `safeguard_prompt` and `pattern_tagging_prompt` with today's seed hashes, and rebuilt the backend. After it ran (`alembic_version` 0102): `safeguard_prompt` still ends with the edit, same `updated_at`; the backend log has "Kept the Admin's edit of safeguard_prompt: the stored text differs from the previous seed, so the new seed text was not loaded. Merge the new seed text into it by hand on the Dashboard."; the unedited `pattern_tagging_prompt` was removed and loaded again from the seed (new `updated_at`). The throwaway migration was deleted and never committed; the stack and the test user were torn down.
- **Checks.** On the final code, on top of main (de0669df): ruff clean, ruff format clean, mypy clean (275 files), pytest 2436 passed.

**Review.** Standards and spec reviews run. Fixed after them: the hash-shape check, the warning's wording (now "Kept the stored <setting>: it differs from the previous seed, as after an Admin's edit, …", since an old seed text never reloaded is kept too), the usage text goes to stderr, and the guide says where to find the warning. These came after the running-app check and are covered by tests only; the app was not run again for them.

**Left as it is, for the owner to know**

- The warning is one line in the backend log, on the deploy that runs the migration. Nothing shows on the Dashboard. Check the log after a deploy that changes a prompt.
- With two backends migrating at the very same moment, the second could print the warning for a prompt the first already reloaded. No text is lost.
- An Admin save that lands in the same instant as the migration's delete can be lost. The old plain delete had the same gap; it is a fraction of a second on deploy.
- The helper compares one previous seed text. A stored prompt from two seed versions back counts as edited and is kept.

**Not done: which prompts on prod differ from today's seed.** This needs a read of the production database, so it waits for the owner's go-ahead. Note that after 0100 and 0101 ran, the prompts those migrations dropped now hold the seed text, so a comparison can show which prompts are edited today but not what was already lost.

### 25 Nov 2026: prod compared with the seed (read only, owner's go-ahead)

Read over `ssh zeph-deploy`: only each text setting's hash, length and `updated_at`, no prompt text. Prod runs main as of 9d1af553 (deployed 24 Nov) and is at migration **0078**. So 0073 and 0078 have run there, but 0080, 0081, 0084, 0086, 0088, 0089, 0092, 0094, 0095, 0096, 0098, 0100 and 0101 have **not**. The "Why" above says they have; that was wrong for these.

Five stored prompts match no version the seed file ever had (all 123 checked), so they are an Admin's edits:

| Setting | Stored | Last saved | Dropped by a waiting migration? |
| --- | --- | --- | --- |
| `reply_plan_prompt` | 25,895 characters | 23 Nov | **Yes**: 0080, 0081, 0084, 0086, 0088, 0095, 0100 |
| `persona` | 8,508 | 20 Nov | No |
| `persona_outlook` | 4,741 | 20 Nov | No |
| `response_prompt` | 6,110 | 24 Nov | No |
| `understanding_prompt` | 14,583 | 23 Nov | No |

- **The next deploy will wipe the edited `reply_plan_prompt`** and load the seed's (14,337 characters), with no warning, because those migrations use the plain delete.
- `curiosity_keeping_prompt`, `pattern_keeping_prompt` and `reply_settings_instructions` are also dropped by waiting migrations, but on prod they still equal the seed, so nothing is lost.
- The seed has not changed since the deploy for the other four edited prompts, so they miss nothing.
- What 0073 and 0078 wiped earlier can't be seen: the edits above were saved after they ran.
- Four stored settings are in no seed any more (`memory_retrieval_prompt`, `sticker_added_reply`, `sticker_already_in_library_reply`, `telegram_already_linked_reply`): leftovers, harmless.

Owner to decide before the next deploy: save a copy of prod's `reply_plan_prompt` and merge it by hand after, or change the waiting migrations to use the helper (they have not run on prod).

## Completion

- Completed: 2026-11-25
- Commit: 14a869e2 (merge of `pattern-28-migrations-keep-prompt-edits` into main; work commits 9682fcfe, 775143a8, 99949e50)
