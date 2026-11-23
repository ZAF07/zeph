# 02 — A cap on the wait from the Message's first text

Status: completed
Track: A
Blocked by: 01

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

However many texts a User sends, no Message waits more than a cap (20s by default) from its first text. Each wait is the rule's seconds (from 01) or the time left to the cap, whichever is shorter, never below zero. The cap counts from the first text of the Message, including texts that joined it through start-over.

`message_wait_cap_seconds` is an Admin setting with a hint, added by migration with its default. It can't be saved below the longest of the three waits.

## Acceptance criteria

- [x] A long burst of trailing texts is answered by 20s after its first text.
- [x] A Message that started over keeps counting the cap from its first text.
- [x] A new Message after a reply has gone out starts its own cap.
- [x] Admins see and can change the cap, with a hint; a cap below any of the three waits is refused.
- [x] Migration adds the setting with its default; no User data is touched. (0076: 20, or the longest stored wait if an Admin set one longer.)
- [x] Tests through the webhook (`FakeTimer.waits`), the Admin settings API, the migration and the Dashboard settings page; all Python and `web/` checks pass.
- [x] `/run`: in a worktree, send trailing texts every ~10s and see the reply come by ~20s after the first.
- [x] `docs/message-pipeline/README.md` step 2 note mentions the cap as built.

## Blocked by

- `.scratch/natural-replies/issues/01-wait-follows-last-text.md`

## Comments

- 23 Nov 2026: built on branch `natural-replies-02-wait-cap`. `PendingMessage.first_text_at` is set when a Message starts (`IncomingMessageHandler._pending_message`, the one place a Message is started); start-over keeps the same `PendingMessage`, so it keeps counting from the first text, and a reply that starts sending (or a crisis drop) forgets it, so the next text starts a new cap. `message_wait` (still pure) now takes `seconds_since_first_text` and returns `max(0, min(rule seconds, cap - seconds since first text))`; `MessageWait.seconds` is now a float. `IncomingMessageHandler` takes the `Clock`.
- Admin rule: `check_waits_fit_under_the_cap` in `core/platform_settings.py` refuses a save that leaves the cap shorter than any of the three waits (so lowering the cap or raising a wait past it), checked against the values after the change. It only runs when a wait or the cap is in the change, so other settings still save if stored values already break the rule. Error: "The Wait cap must be at least the longest wait (N seconds)."
- Review decisions: the first version leaned on the seed to add the setting (as issue 01 did); the spec review pointed out an install whose Admin had a wait over 20s (`message_wait_seconds` allowed up to 30 before 01) would get its wait silently cut. Migration **0076** now adds the cap at `GREATEST(20, longest stored wait)`; the seed still holds 20 for new installs. Also from review: one `_pending_message` helper instead of three `setdefault` copies; `MESSAGE_WAITS` sits with the setting constants.
- Known small gap (spec review, accepted): the cap counts from when the first text's work starts on the User's line of texts, not from the webhook call; with a busy line this starts the cap slightly late.
- The cap counts screening time: a text whose Safeguard check finishes past the cap is answered straight after the check (wait 0), not before it. Seen in a /run where the third text came at 18s and its check took 5.6s: answered at 23.6s.
- Not done here: worktree `.env` had `PRODUCTION_DOMAIN= <value>` (space after `=`), copied from the main `.env` line 76, which breaks `set -a; . ./.env` in `run-dashboard/start-session.sh`. Fixed only in the worktree copy; the main `.env` still has it.

## Evidence

- Long burst (`/run`, worktree backend on load-test adapters, real `ThreadTimer` and webhook; times from `model_calls.started_at`): trailing texts at 0s and 10s → second Safeguard done at 15.95s, Understanding started at **20.03s** (no cap: 27.95s). Texts at 0/9/18s → last check done 23.62s, Understanding 0.02s later (no cap: 35.6s). Test: `test_a_long_burst_of_trailing_texts_is_answered_by_the_cap_from_its_first_text` (waits 13, 11, 2, 0), `test_a_finished_text_near_the_cap_waits_only_the_time_left` (1.5).
- Start-over keeps the cap (`/run`): "hey" at 0s → Understanding at 9.86s; "and" at 15.0s dropped that try (2 Understanding calls, 1 Reply Plan, 1 text sent); "and" checked at 18.60s → new Understanding at **20.04s** (a new cap would give ~30.6s). Test: `test_a_message_that_started_over_keeps_counting_the_cap_from_its_first_text` (7 then 5).
- New Message after a reply (`/run`): "so" after the earlier reply went out → checked at 57.92, Understanding 12.05s later (full trailing wait; an old cap would give 0). Test: `test_a_new_message_after_a_reply_has_gone_out_starts_its_own_cap`.
- Admin settings: API tests in `tests/test_admin_settings.py` (seeded 20 with a hint; 61 refused; cap 11, trailing 21, finished 25, wait 30 + cap 25 refused with nothing saved; trailing 30 + cap 30 saved together; unrelated save allowed with a stored wait past the cap). Dashboard (`/run`, run-dashboard as Admin, 1280 and 390): "Wait cap" row in Conversations, 20 sec, hint shown; saved 30 → 30 after reload; 5 → "The Wait cap must be at least the longest wait (12 seconds)." and still 30 after reload; put back to 20; no page errors. Vitest: `PlatformSettingsForm.test.tsx` shows/saves the cap and shows the refusal.
- Migration: `tests/test_message_wait_migration.py` (from 0075: cap 20 with Admin's 9s kept; Admin's 25s trailing → cap 25). `/run` through real backend start-up from 0075: trailing 25 → cap 25; default waits with 2 Users / 16 messages / 2 Conversations / 2 connections → cap 20, counts and an md5 of every `conversation_messages` row identical before and after.
- Checks after rebase on main (with issue 05): `ruff check`, `ruff format --check`, `mypy` (217 files) clean; `pytest` 1632 passed; web `pnpm lint`, `format:check`, `typecheck` clean, `pnpm test` 904 passed, `pnpm build` compiled. Rebased stack started healthy at 0076 with cap 20.
- Docs: `docs/message-pipeline/README.md` decision 19 ("the cap too") and step 2 note describe the cap as built, with migration 0076.


## Completion

- Completed: 2026-11-23
- Commit: a279e3f (merge "Merge natural-replies-02-wait-cap: a cap on the wait from the Message's first text"; work in b1d373d "Natural replies 02: a cap on the wait from the Message's first text", 279127e "Natural replies 02: review fixes (migration 0076 adds the cap, never below a stored wait; one helper starts a Message)", 2b6a8ca "Archive natural-replies issue 02: wait cap verified")
