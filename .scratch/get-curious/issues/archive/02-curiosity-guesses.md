# 02 — Curiosity guesses

Status: completed

## Parent

`.scratch/get-curious/PRD.md`

## What to build

A Curiosity can hold a **guess**: something Zeph suspects about the User but isn't sure of (e.g. "their mum lives in Singapore"), with **how sure** it is (low, medium or high). See ADR-0017 and the Curiosity entry in CONTEXT.md.

- **Keeping.** When a Conversation ends, the Curiosity-keeping step may write a guess for something the User hinted at without settling, or something Zeph may have got wrong. It closes a waiting guess once the User answered it in that Conversation. The usual Memory Item keeping saves what they said, so the answer is never written as a new guess.
- **Showing.** The Understanding sees a due guess Curiosity with its guess and how sure Zeph is, marked as not known and to be checked gently. When one is raised, in a reply or in the Curiosity Check-in, the reply or Check-in is told it's a guess to check, never a fact to state.
- **Limits.** Guesses share the existing Curiosity waiting limit and per-Conversation raise limit.
- **Privacy.** Users never see guesses. Delete My Data, Account Deletion and deleting the source Memory Item or Life Thread remove them, as for any Curiosity. No new guesses are made while User Memory or Curiosities don't work for the User.

The Curiosity-keeping prompt is reloaded from the seed by the migration, as earlier prompt migrations do.

## Parallel work: avoid clashes

Issue 01 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 01 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Understanding code:** you own how due Curiosities are written out for the Understanding and the reply, and the Curiosity Check-in wording. Don't touch which Moves are offered or how Moves are recorded; 01 owns that.
- **Platform settings seed:** you edit the Curiosity-keeping prompt (and any Curiosity wording shown to the Understanding or reply). 01 edits only the Woven-in Check-in wording.
- **Models and tables:** you change Curiosity only; 01 changes Move.
- Issue 04 later also edits the Curiosity-keeping prompt (look-backs). Leave a clean place for it; don't add look-backs here.

## Acceptance criteria

- [x] Curiosities have optional guess and how-sure fields, added by a migration; plain Curiosities leave both empty
- [x] The Curiosity-keeping prompt explains guesses and asks for them in its JSON shape; the migration reloads it from the seed
- [x] A guess from the keeping step is saved with how sure Zeph is (Conversation-end test with the scripted chat model)
- [x] An answered waiting guess is closed by the keeping step
- [x] A due guess is shown to the Understanding as a guess with how sure Zeph is, to check gently (webhook test)
- [x] A raised guess tells the reply to check it, never state it; the Curiosity Check-in does the same
- [x] No guesses are made while User Memory or Curiosities don't work for the User
- [x] Delete My Data and deleting the source Memory Item remove guesses (test)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] `/run`: in the running app, end a real Conversation where the User hints at something without settling it, and see a guess saved in the curiosities table. Then, in a new Conversation, the Understanding call shows it as a guess, and the User's answer closes it at that Conversation's end. Shift timestamps instead of waiting for the quiet gap

## Blocked by

None - can start immediately.

## Comments

- 2026-11-18 evidence, per criterion:
  - Guess and how-sure fields: migration `0058_curiosity_guesses.py` adds nullable `guess` and `how_sure` to `curiosities`; `Curiosity` and `CuriosityToRaise` carry them, `None` for plain ones. Tests: `test_the_guesses_migration_adds_empty_columns_and_reloads_the_keeping_prompt`, and the plain Curiosity in `test_a_guess_from_the_keeping_step_is_saved_with_how_sure_zeph_is` has both empty.
  - Prompt: the seed's Curiosity-keeping prompt has a guess bullet and a guess entry in its JSON shape (`"guess"`, `"how_sure": "low" | "medium" | "high"`); closing an answered guess is folded into the existing close bullet. 0058 deletes the stored prompt so it reloads from the seed. Look-backs (issue 04) can go in as their own bullet after the guess bullet.
  - Saved with how sure, and an odd how-sure read as low: `test_a_guess_from_the_keeping_step_is_saved_with_how_sure_zeph_is`.
  - Answered guess closed: `test_an_answered_waiting_guess_is_closed_by_the_keeping_step` (the keeper is shown `Guess (how sure: medium): ...`).
  - Shown to the Understanding: `test_a_due_guess_is_shown_to_the_understanding_as_a_guess_to_check_gently` (webhook). One wording for all three places: "A guess, not known: <guess> (how sure: <x>). Check it gently; never state it as fact."
  - Reply and Curiosity Check-in: `test_a_raised_guess_tells_the_reply_to_check_it_never_state_it`, `test_a_curiosity_check_in_asks_a_guess_as_a_gentle_check`.
  - No guesses while User Memory or Curiosities don't work: the keeper only runs when both work (`post_conversation.py`); `test_no_guesses_are_made_while_user_memory_or_curiosities_do_not_work`.
  - Deletion: `test_delete_my_data_and_deleting_the_source_memory_item_remove_guesses`. Account Deletion and Life Thread deletion use the same row cascade, untouched.
  - Checks: `uv run ruff check .` all passed, `uv run ruff format --check .` 450 files formatted, `uv run mypy src` no issues in 182 files, `uv run pytest` 1293 passed.
- 2026-11-18 review: Standards found no hard breaches; fixed the duplicated how-sure fallback (`how_sure_word`). Spec found one piece of scope creep (updating a waiting guess, never offered by the prompt); removed. Kept two plain fields rather than a `Guess` type, since the issue asks for two optional fields that map one to one to the columns.
- 2026-11-18 `/run` (worktree stack, fresh database migrated to 0058 on start; the main stack was down, so `make db-copy` couldn't run and a test User was added with SQL). Two real Conversations went through `/telegram/webhook` with `create_app`, real repositories, DeepSeek and fastembed inside a backend container; only Telegram (recording channel), the timer and the scheduler were swapped. Conversation ends were brought on by moving `last_message_at` back two hours and ticking the scheduler.
  - First try: the mum message from the PRD saved no guess, because Memory keeping already stored "Their mother lives in Singapore" (right). A ward shift message also saved none, so the guess bullet was made clearer about what hints to look for (job, who someone is, where someone lives, a routine). Then:
  - Conversation 1, "finally home. 12 hours on my feet and the ward was chaos again, three new admissions right before handover": keeper answered `"guess": "their ward is short-staffed at the moment", "how_sure": "low"`; the curiosities row has `guess = 'their ward is short-staffed at the moment'`, `how_sure = 'low'`, `waiting`.
  - Conversation 2, "hey, quick hello before my shift tonight": the Understanding was shown `[1] Is the ward short-staffed at the moment, ...? ... Sensitivity: low. A guess, not known: their ward is short-staffed at the moment (how sure: low). Check it gently; never state it as fact.` It chose not to raise it (Just chatting, a quick hello). Then "honestly yes, we've been two nurses down since October and nobody's been hired yet"; at the Conversation's end the keeper answered `{"curiosity": 1, "close": true}`, the row is `closed`, and Memory keeping saved "Their ward has been two nurses short since October with no new hires", with no new guess.
  - Not seen live: a guess raised in a reply (the Understanding didn't raise it). Covered by the webhook test above.
  - Caveat, outside this issue: an earlier try's message "back on the ward again tonight, ugh" set off the Safeguard's Crisis Reply. Looks like a false positive in shipped code; worth a `/file-bug`.

## Completion

- Completed: 2026-11-18
- Commits:
  - `e7e484f` Get-curious issue 02: Curiosities can hold a guess with how sure Zeph is
  - `45a72a1` Get-curious issue 02 review fixes: drop unused guess update, share how-sure wording, fold close into the existing bullet
  - `30b8327` Get-curious issue 02: keeping prompt says what hints to guess at, so the real model writes guesses
  - `be3d78f` Get-curious issue 02 done: archive issue with check, review and run evidence
  - `465ce4e` Merge get-curious issue 02 into main
