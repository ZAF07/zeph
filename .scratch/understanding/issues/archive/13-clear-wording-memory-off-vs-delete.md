# 13 — Clear wording: User Memory off vs Delete My Data

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Users must understand that User Memory off never deletes anything (it only stops learning) and that Delete My Data removes everything, private notes included. All wording is Admin-editable seed text.

- **Consent** (Onboarding): the User Memory explanation gains an honest line that the Companion also keeps private notes to follow up with them, which they won't see and which Delete My Data removes. It no longer claims everything is listed on the Dashboard.
- **Turning User Memory off in chat:** the confirmation always includes a fixed Admin-set line ("Nothing is deleted. I'll still use what I know, I just won't learn anything new. Use Delete My Data to remove everything.").
- **Delete My Data prompts** (chat and Dashboard) say they remove all memories and private notes.
- Dashboard notes for memory off already say it stops learning; check they mention Delete My Data.

## Acceptance criteria

- [x] Seed wording updated; each line editable by Admins
- [x] Turning User Memory off in chat always sends the fixed line (webhook-seam test with scripted settings tool call)
- [x] Delete My Data prompts mention private notes, in chat and on the Dashboard (backend and Vitest tests)
- [x] Settings Eval still passes
- [x] Checks pass (backend and `pnpm`)
- [x] `/run`: turn memory off in chat and see the fixed line; `/run-dashboard`: see the consent and Delete My Data wording

## Blocked by

- `.scratch/understanding/issues/11-curiosities.md`

## Decisions

- The memory-off line is sent by the backend, not left to the model: the settings tool sets `ReplyOffer.closing_text`, and response composition adds it as the last text message of the reply. Turning memory back on in the same reply drops it. The tool result tells the model the line is sent for it, so it shouldn't repeat it.
- The memory-off tool's own wording was out of date ("stops saving or using it"). It now says off deletes nothing and keeps using what is saved, which matches stories 48–49.
- New Admin-editable settings, all on Settings except the chat note: `memory_off_chat_line`, `delete_my_data_description` (served on `/api/platform-content`), `data_deleted_reply` (existed, now editable), and `data_deletion_started_note` (was hardcoded in the tool; must keep `{word}`; on Prompts and Models under "Settings in chat").
- Migration 0034 reloads `user_memory_explanation`, `memory_paused_note`, `memory_not_available_note` and `data_deleted_reply` from the seed (platform not live, so no Admin edits are lost).
- The Dashboard type-DELETE confirmation box is unchanged; the description above it is the Delete My Data prompt.

## Evidence

- **Seed wording, each line editable:** `tests/test_memory_off_and_delete_wording.py` — consent mentions private notes and Delete My Data and drops "Everything I remember is listed"; memory-off notes point to Delete My Data; `test_admins_can_edit_the_memory_off_and_delete_my_data_lines` edits all four new/changed lines through `PATCH /api/admin/settings` and sees them in chat and on platform-content; `{word}` is required (422 without it); `test_an_existing_install_reloads_the_reworded_settings` (migration 0034).
- **Memory off in chat always sends the fixed line:** `tests/test_settings_via_chat.py::test_turning_user_memory_off_in_chat_always_sends_the_fixed_line` (webhook seam, scripted `turn_user_memory_on_or_off` call; texts sent are the reply then the fixed line; turning it on sends no line) and `test_the_memory_off_line_is_not_sent_when_memory_was_not_turned_off`.
- **Delete My Data prompts mention private notes:** chat — `test_delete_my_data_in_chat_only_deletes_after_the_confirmation_word` asserts "private notes" in the tool result; `test_delete_my_data_wording_mentions_private_notes` (platform-content description, data deleted reply, started note). Dashboard — `AccountSettings.test.tsx` "says what Delete my data removes, private notes included"; `PlatformSettingsForm.test.tsx` "shows and saves the memory-off line and the Delete my data wording".
- **Settings Eval:** 14 of 14 right against DeepSeek (memory-off and delete-my-data cases included).
- **Checks:** `pytest` 886 passed; `ruff check`, `ruff format --check`, `mypy` clean; `pnpm lint`, `format:check`, `typecheck` clean; `pnpm test` 371 passed.
- **/run (chat):** real app in the worktree backend container with the real DeepSeek model and Postgres (migration 0034 applied); only the Telegram channel was a recorder, auth a fixed token, the timer ran work at once (worktree Telegram can't reach a fake chat). User onboarded and connected through the real API and `/start`. "please stop remembering things about me" → "Done — I've turned off memory, so I won't be picking up anything new about you from here on." / "Nothing I already had was deleted, though, if you want that gone too." / "Nothing is deleted. I'll still use what I know, I just won't learn anything new. Use Delete My Data to remove everything." (memory now off). "delete all my data please" → "…your messages, everything I remember about you, the private notes I keep to follow up, your stickers, your Check-ins and this Telegram connection…" / "Reply with exactly DELETE…". "DELETE" → the new data deleted reply with "my private notes".
- **/run-dashboard:** signed-in Admin, worktree web on 3210, no page errors. Onboarding Memory step shows the new third paragraph ("I also keep a few private notes to follow up with you… Delete My Data removes them along with everything else."). Account & privacy → Your data shows the new description with private notes. Admin Settings shows "“Memory off” line in chat", "“Delete my data” description" and "“Data deleted” reply" with their seeded values.
- **/code-review:**
  - Standards: no hard breaches. Fixed: migration keys as one SQL tuple like 0032; seed lines wrapped. Kept: the tool setting `closing_text` on its offer follows how `picked` already works; the new Dashboard field follows the existing platform-content path.
  - Spec: nothing missing. Fixed: Delete My Data wording now also lists stickers, as CONTEXT.md does. Making `data_deleted_reply` editable kept (story 64).

## Completion

- Completed: 2026-11-14
- Commits: `d6b3757` (wording, settings, closing line, migration 0034, tests), `8577be5` (review fixes: stickers in Delete My Data wording, migration style, seed wrap), `5fa97f6` (issue archived with evidence)
- Merged into main: `81fa5d9` (branch `understanding-13-clear-wording`, pushed to origin)
