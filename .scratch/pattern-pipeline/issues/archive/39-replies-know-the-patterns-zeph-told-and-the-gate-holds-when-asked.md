# 39 — Replies know the Patterns Zeph told the User, and the gate holds when they ask

Status: completed
Track: shared
Blocked by: 37 (the wording a User was told)

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answer 1 and the owner's two added items on told Patterns.

## What to build

1. **Replies are shown the told Patterns.** While Pattern sharing works and they aren't struggling, the Reply Plan is shown the Patterns Zeph told the User that are being tested or confirmed: the wording they were told, where it shows, and which of the two it is. It may build its Read on one and name it when today's story fits (`named_pattern`); the reply then says "the thing we're testing" for one being tested and states a confirmed one plainly, always as Zeph's view. Never a Pattern they disagreed with (those keep their own list and rule).
2. **Where each told Pattern showed up.** From the Observations tagged at each Conversation end (no new model call), code works out for each told Pattern where it last showed up and where they last acted against it (day, who, Life Thread), and the Reply Plan is told with each Pattern.
3. **The gate wins when they ask (answer 1).** The Reply Plan says when the User asks what patterns Zeph sees in them (`asked_for_patterns`). Then: a Pattern offered for sharing is shared; else a told Pattern may be talked about; else code tells the reply to say it is still getting to know them and that it may talk about one recent situation, never a claim about who they are. The Agenda's if / then stays shown to the Reply Plan.
4. **An Understanding Eval case** for the ask with nothing ready. Evals cost money: the owner is asked before any run.

## Acceptance criteria

- [x] The Reply Plan is shown shared and confirmed Patterns with where they last showed up, never contested ones, and none while struggling or while Pattern sharing is off, with tests
- [x] A reply that names a told Pattern is given its wording and how to say it, with a test
- [x] Asked for patterns with nothing ready or told, the reply is told to say it is still getting to know them, with a test; with a Pattern ready, it is offered for sharing as before
- [x] An Understanding Eval case covers the ask; the owner was asked before any run
- [x] `docs/pattern-pipeline/README.md`, `docs/message-pipeline/README.md` and `CONTEXT.md` say what changed
- [x] `ruff`, `ruff format`, `mypy` and `pytest` pass, and it was checked in the running app

## Comments

### 25 Nov 2026: built

Review fixes: when Zeph has no Pattern it may tell (none told, or Pattern sharing off, or the User is struggling), the reply is told "You have no pattern you may tell them now", not that nothing was noticed; evidence that only narrows a told Pattern is not shown as "acted against".

**Eval runs (the owner said yes to each).** Case `asked-for-patterns-nothing-ready`, real models:

| Run | Reply Plan and Reply model | Passed | Cost |
|---|---|---|---|
| `b3e02c71`, `eb3cef1b`, `0a3eed92` | deepseek-v4.1-flash (live) | 3 of 3 | S$0.024 (estimate S$0.007 to S$0.009 each) |
| `898e711d` A | deepseek-v4-pro | 1 of 3 | about S$0.13 |
| `898e711d` B | claude-fable-5.2 | 1 of 3 | about S$0.71 |
| `898e711d` C | claude-opus-5.5 | 3 of 3 | about S$0.33 |

In all 12 tries the Reply Plan read the ask (`asked_for_patterns` true), code gave the reply the fixed section, and the reply said it had no pattern yet and was still getting to know them. The 4 fails are the same thing: the made-up User had told no story in the Conversation, so the reply gave a view of the ask itself ("you'd rather hear something true than something nice", "maybe you're checking whether I pay attention"), which the Judge read as a claim about them. The section now says to give no view when no situation was told. That change has not been run against a real model. The run's estimate (S$0.07 for the 9 tries) was far under its cost (about S$1.2): the estimate doesn't price a Variant's dearer model.

**Checks.** ruff clean, ruff format clean, mypy clean (286 files), pytest 2584 passed; web: eslint, prettier and tsc clean, Vitest 989 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0109, seeds loaded). Dashboard pages were driven in a real browser as a signed-in Admin and User. The chat path was run by the real core services on the stack's database with only the chat model scripted, the chat channel recording, and the clock and scheduler moved by hand (a worktree can't reach Telegram), acting as the signed-in User so the browser showed the result. Not checked: the migrations on a copy of the main database (the main stack wasn't running); the tests cover them by downgrading and migrating again.

**Evidence per criterion**

- **The Reply Plan is shown shared and confirmed Patterns with where they last showed up; never contested; none while struggling or with sharing off.** `tests/test_told_patterns_in_replies.py` (13 tests). Running app: two days after sharing, the Reply Plan's input held "Patterns you have told them … [1] (being tested) You seem to protect closeness… It shows with family, friend; not with partner. Last showed up: 12 Oct 2026, about Jun, a friend."
- **A reply that names a told Pattern is given its wording and how to say it.** `test_the_reply_plan_is_shown_the_pattern_zeph_told_them_and_may_name_it`. Running app: with `named_pattern` 1 the reply's instructions held "What they are telling you now links to something you told them before: … call it something like “the thing we're testing”".
- **Asked with nothing ready or told → still getting to know them; with one ready → shared.** `test_asked_for_patterns_with_nothing_ready…`, `…_a_ready_one_is_shared_even_if_the_plan_did_not_say_so`, `…_after_one_was_told_the_reply_recalls_it_and_no_other`. Running app: with a Pattern only suspected, the reply was told "You have no pattern you may tell them now. Say plainly that you are still getting to know them…"; with one told, it was given that Pattern and "Tell them no other pattern". Real model: the table above.
- **An Understanding Eval case; the owner was asked before any run.** `asked-for-patterns-nothing-ready` in the seed; asked once for the 3 live runs, and the owner asked for the three-model comparison.
- **Docs.** `docs/pattern-pipeline/README.md`, `docs/message-pipeline/README.md`, `docs/pattern-evals/README.md`, `CONTEXT.md` (Read, Pattern), ADR 0030.
- **Checks pass; checked in the running app.** Above.

## Completion

- Completed: 2026-11-25
- Commit: efe99ea5 ("Merge pattern-30-owner-decisions-before-sharing: the owner's decisions before Pattern sharing is on", the merge of pattern-30-owner-decisions-before-sharing into main; work commits b4fdc35d, 351f74c8, ec11f7a8, e21f096b, f9225f60, 7522ee99, 45d716a0, cc0fd499, ff840919, 875f3175, 88bc0a4a)
