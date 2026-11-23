# 05 — The Safeguard and Recall use Replied-to Texts

Status: completed
Track: B
Blocked by: 04

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

- **Safeguard:** reads each text with its Replied-to Text as it arrives, in the same call. A "yes" sent as a reply to Zeph asking about self-harm must be read with that question. It is still checked as the text arrives, never held back by the wait.
- **Recall:** the search text for Life Threads, Patterns and Move Outcomes adds the Replied-to Texts of the Message's texts to what the Understanding says the User means and the latest texts. A reply to a weeks-old text brings back the Thread it was about.

## Acceptance criteria

- [x] The Safeguard's prompt for a text includes its Replied-to Text.
- [x] "yes" as a reply to Zeph's self-harm question gets the Crisis Reply (fake model set to flag it; the test checks the question reached the Safeguard).
- [x] Recall's search includes the Replied-to Text, and a Thread close only to the replied-to text comes to mind.
- [x] A text with no Replied-to Text is checked and searched as today.
- [x] Tests through the webhook (fake chat model prompts, fake embeddings); all Python checks pass.
- [x] `/run`: in a worktree, reply to an old Zeph text about a known Thread and see that Thread among those reminded in the trace.
- [x] `docs/message-pipeline/README.md` decision 20 note updated to "Built".

## Blocked by

- `.scratch/natural-replies/issues/04-zeph-reads-replied-to-texts.md`

## Comments

**Done, 23 Nov 2026.** Evidence per criterion:

- Safeguard prompt includes the Replied-to Text: `test_the_safeguard_reads_a_text_with_its_replied_to_text`, `test_the_safeguard_reads_a_photo_with_its_replied_to_text` (photo path, where the Safeguard's text is swapped for the description). `/run` Safeguard call: `Person: (replying to the Companion's text from 30 Oct 2026, "did the landlord ever get back to you about the studio deposit?") nope, still nothing. so annoying`.
- "yes" replying to the self-harm question gets the Crisis Reply: `test_yes_as_a_reply_to_zephs_self_harm_question_gets_the_crisis_reply`. `/run` with the real Safeguard model: the reply got the Crisis Reply and a `suicide_or_self_harm` Safeguard Event; a bare "yes" got a normal reply and no event.
- Recall searches by it and a Thread close only to it comes to mind: `test_recall_searches_with_the_replied_to_text`, `test_a_thread_close_only_to_the_replied_to_text_comes_to_mind` (both red before the change, green after). `/run` with real embeddings: "Moving out of the shared flat" was reminded in the Reply Plan for the reply, not for the same text sent plainly.
- No Replied-to Text, checked and searched as today: `test_texts_with_no_replied_to_words_are_searched_as_today`; existing `tests/test_safeguard.py`, `tests/test_life_threads.py`, `tests/test_patterns*.py`, `tests/test_move_outcome_recall.py` pass unchanged.
- Tests and checks: `ruff check`, `ruff format --check`, `mypy` clean; `pytest` 1576 passed on the branch, 1619 after rebasing on main (with issue 01).
- `/run` in the worktree: real backend app, Postgres, embedder and chat model in the backend container; the chat channel swapped for a recording one so nothing went to Telegram.
- Decision 20 note in `docs/message-pipeline/README.md` now says built for the Safeguard and Recall.

Decisions and caveats:

- `recent_texts_to_search` in `core/life_threads.py` (renamed from `recent_incoming_texts`) puts each recent text's Replied-to Text before it. It takes the last N texts first (Admin setting), so a reply older than those N drops out with its Replied-to Text, the same as texts did before.
- The Replied-to Text also goes into name matching for Life Threads, so a name in Zeph's old text can bring back a Thread by name.
- Patterns only search when the User has Patterns, so with none only the Life Threads and Move Outcomes searches run.

## Completion

- Completed: 2026-11-23
- Commit: edbb74c (merge of 1afad3e "Natural replies 05: the Safeguard and Recall use Replied-to Texts", 4197b0b "Natural replies 05: review fixes", 77f928c "updated tasks status")
