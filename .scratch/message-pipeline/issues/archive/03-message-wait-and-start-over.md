# 03 — A Message waits for the User to finish, and starts over

Status: completed
Lane: A
Blocked by: 01

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

People say one thing across several texts. Two changes:

- The Message wait (`message_wait_seconds`, Admin-set) gets a longer default: 15 seconds instead of 5.
- If a text arrives while a reply is being prepared and before any part of it has been sent, the reply in progress is dropped and the Message is answered again with every text in it. A Woven-in Check-in already saved for the dropped reply is taken back (the existing take-back path), so it stays due. Once any part of a reply has been sent, a new text starts the next Message, as today.

The Safeguard still checks each text as it arrives; a crisis gets the Crisis Reply at once and is never held back by the wait. This works inside the in-memory per-User queue (ADR-0032); no change to how many processes run. Update the **Message** term only if the code forces a wording change (it already describes this).

User stories covered: 1, 2, 3, 8.

## Acceptance criteria

- [x] The default Message wait is 15 seconds for new installs and the setting's seed is updated
- [x] A text arriving mid-write, before anything is sent, means one reply that answers every text, and no reply goes out for the dropped attempt
- [x] A Woven-in Check-in saved for a dropped reply is taken back and stays due
- [x] A text arriving after part of a reply has been sent starts the next Message
- [x] A crisis text sent during the wait still gets the Crisis Reply at once
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 01 — Reply follows a strict priority order (`.scratch/message-pipeline/issues/01-reply-priority-order.md`)

## Comments

### 20 Nov 2026: implementation and evidence

**What was built**

- Seed `message_wait_seconds` is 15 (it was 4 on main, not 5 as written above). Migration 0066 deletes the stored value only where it is still 4, so the seed reloads; an Admin's own value stays.
- `core/reply_attempt.py`: `ReplyAttempt` is one try at answering a Message. A new text drops it until sending starts. `start_sending()` runs right before each part, photo or sticker goes out (`before_sending` in `ConversationService.deliver_reply`), and a dropped try raises `ReplyDroppedError` there, so nothing is sent. `apply_house_rules` runs the ReplyGate once per Message while the try can't be dropped, and keeps the result, so a Message started over counts once toward the Daily Message Limit, and a Message the gate stops (Limit Reply, data deleted) is settled at once.
- `IncomingMessageHandler`: the one per-User lock became two, one for checking texts and one for writing replies. A text is checked by the Safeguard at once even mid-reply, and drops the reply in progress before joining the Message. The Message stays waiting until the reply starts being sent, so a dropped try leaves every text in place, and the new text restarts the wait. A crisis (text or Album) drops the whole Message, so nothing is answered normally.
- `ReplyService.handle` takes the attempt and checks it between steps. A drop raised inside its `try` goes down the existing take-back path, so a saved Woven-in Check-in is taken back and stays due.

**Per criterion**

1. 15 second default: seed `src/companion/seed/platform_settings.yaml`; `test_the_message_wait_is_editable_with_a_seeded_value_of_fifteen_seconds`; migration tests `tests/test_message_wait_migration.py` (reloads old seed / keeps an Admin's value). Live: a fresh worktree database had `message_wait_seconds = 15` at version 0066. The copied main database (Admin had set 5) migrated to 0066 and kept 5.
2. One reply to every text, none for the dropped try: `test_a_text_sent_while_a_reply_is_written_starts_it_over_with_every_text`, `test_an_album_photo_sent_while_a_reply_is_written_starts_it_over`, `test_a_message_started_over_counts_once_toward_the_daily_limit`. Live (scenario A, run twice, the second time after the review fixes): "ugh work was a lot today", then "my manager moved the deadline up again" sent while Reply call 1 was running. Sent after the dropped try: `[]`. Reply call 2 saw "ugh work was a lot today\nmy manager moved the deadline up again", and one reply went out. Daily message count 227 → 228.
3. Woven-in Check-in taken back: `test_a_woven_in_check_in_for_a_reply_started_over_is_taken_back_and_stays_due`. Live (scenario B, twice): with the Check-in model forced to weave in, a Check-in row was saved while the reply was written; "pasta again lol" dropped the reply; sent `[]`; after the restart, Check-ins kept: `[]`, and the next Due Time was the same before and after.
4. After part sent, next Message: `test_a_text_sent_after_part_of_a_reply_went_out_starts_the_next_message`. Live (scenario C): "thanks" came in after the first of two parts was sent. The second part still went out, then a separate reply ("Go eat while it's hot.") answered the next Message.
5. Crisis during the wait: `test_a_crisis_text_gets_the_crisis_reply_at_once_and_the_rest_is_not_answered`, plus the new `test_a_crisis_text_sent_while_a_reply_is_written_gets_only_the_crisis_reply`. Live (D): "hey" then "honestly i want to kill myself" got the Crisis Reply before the wait ended; 0 reply calls after the wait. Live (E, in a new Conversation from 02:01:18): the reply to "long day" was being written when "i don't want to be alive anymore" came in. The Crisis Reply went out 1.2s later, and no normal reply was sent. (An E run inside the Conversation that already held D's crisis isn't counted: the Safeguard rightly read "long day" in that context as crisis.)
6. One migration head: rebased on origin/main (a64c15a, after issue 06 merged); main's latest migration is 0065, and 0066 is the only one after it.
7. Docs: `docs/message-pipeline/README.md` step 2's "Today" note became a "Built (20 Nov 2026)" note. The **Message** term in `CONTEXT.md` already describes this, so it is unchanged. ADR-0032 gained one Consequences line about the two locks.
8. Checks after rebasing on a64c15a: `uv run pytest` 1372 passed; `ruff check` all checks passed; `ruff format --check` 536 files already formatted; `mypy src` no issues in 193 source files.
9. `/run`: worktree stack `ai-chat-companion-mp-03` with `make db-copy` data. The real app (`create_app` with the real builders) ran inside the backend container, with real repositories and the real DeepSeek models, through `/telegram/webhook`. Swapped out: the chat channel (records sends), the timer (Message waits ended by hand, typing waits skipped) and the scheduler (manual). In B only, the Check-in model's answer was forced to "weave in". Conversations were moved back past the quiet gap to start new ones (no waiting).

**Code review** (Standards and Spec, in parallel). Fixed in the second commit:
- The gate stopping a reply while a text drops it could send a second Limit Reply: the house rules now run while the try can't be dropped.
- An Album crisis with a text arriving at the same time left earlier texts to be answered: now the whole Message is dropped.
- An Album photo could be lost: it now drops the reply before joining the Message.
- Ending a try and forgetting its Message now happen under one guard.
- Smaller fixes: `drop()` returns nothing; the house rules are kept as `ReplyNeeded | None`, not a `None` note; `_answer` became `_try_answer`; Album items are removed by identity.
- Added `tests/test_reply_attempt.py` and the Album mid-write test.

**Caveats**

- The owner's main database keeps its Admin-set wait of **5 seconds**; the migration doesn't override Admin edits. Set it to 15 on the Dashboard to get the longer wait.
- While the house rules run (a database call, and the Limit Reply when over the limit), a new text waits briefly before it is checked.
- The per-User locks are never cleaned up (this was already so before; now there are two maps).

## Completion

- Completed: 2026-11-20
- Commit: e099a96 "Merge message pipeline issue 03: the Message wait is 15 seconds by default (migration 0066 reloads it only where still at the old seed); a text that arrives while a reply is written, before any of it is sent, drops that reply and the Message is answered again with every text, its Woven-in Check-in taken back and counted once toward the Daily Message Limit; texts are checked by the Safeguard at once, even mid-reply; a text after part of a reply was sent starts the next Message"
- Branch commits: 2a5f245 (wait and start over), 327b9c7 (review fixes), 0f1fcc8 (archive), 9619107 (evidence after rebase)
