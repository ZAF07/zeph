# 01 — The wait follows how the last text reads

Status: completed
Track: A
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/archive/PRD.md`

## What to build

Today every text restarts one 15s wait. Make the wait depend on how the User's latest text reads:

- **Finished**: ends with `?`, or is at least the "long" word count and ends with `.`, `!` or an emoji → short wait (2s).
- **Trails off**: ends with `...`, `…` or `,`; or its last word is in the trailing words list; or the whole text is one of the short openers in that list (`wait`, `ok so`, `lol`, `hmm`, …); or a photo with no caption → long wait (12s).
- **Neither**: anything else, including a sticker alone → middle wait (6s).

Matching ignores case and trailing spaces. An Album still waits for all its items, then is judged as one text. Start-over (a text before any reply has gone out drops the reply) stays as it is.

Admins set the three waits, the long-text word count and the trailing words list on the Platform settings page. Each setting has a hint (one or two sentences) saying what it is and how it changes Zeph's replies, e.g. *"How long Zeph waits for more when the User's last text ends unfinished ("and…", "so"). Longer means fewer cut-offs but slower replies."* `message_wait_seconds` stays as the **neither** wait with a rewritten hint.

A migration adds the new settings with their defaults and moves `message_wait_seconds` from 15 to 6 only where it is still the seeded 15 (as migration 0066 did). No User data is touched.

The deciding logic should be one small pure function (text + settings → kind and seconds).

## Acceptance criteria

- [x] A text ending in `?` gets the finished wait; a 15+ word text ending in `.`, `!` or an emoji gets it too.
- [x] A text ending in `...`, `…`, `,` or a trailing word, a short opener on its own, and a photo with no caption each get the trailing wait.
- [x] Any other text, and a sticker alone, gets the neither wait.
- [x] A text sent before any reply goes out still starts the reply over with every text.
- [x] An Album is still answered as one, judged as one text once all its items are in.
- [x] Admins see and can change all five new settings and `message_wait_seconds`, each with a non-empty hint of at most two sentences; bad values are refused (seconds 0–60, words 1–100, list not empty).
- [x] A changed setting applies from the next text.
- [x] Migration: new settings land with defaults; `message_wait_seconds` 15 → 6 only if unchanged; an Admin's own value is kept.
- [x] Tests through the webhook (`FakeTimer.waits`), the Admin settings API, the migration and the Dashboard settings page; `pytest`, `ruff`, `ruff format`, `mypy`, and the `web/` checks pass.
- [x] `/run`: in a worktree, post texts to the backend webhook and see a `?` text answered after ~2s and a trailing text held ~12s.
- [x] `docs/message-pipeline/README.md` step 2 note and decision 19 updated to "Built".

## Blocked by

None - can start immediately.

## Comments

- 23 Nov 2026: built on branch `natural-replies-01-wait`. The rule is `message_wait` in `src/companion/core/message_wait.py` (pure: kind + text + settings → how it reads + seconds), called from `IncomingMessageHandler._restart_wait`. An Album item judges the Album so far (same `album_id`) as one photo text by its caption. New setting kind `text_list` for the trailing words (trimmed, lower-cased, blanks dropped, not empty); the Dashboard edits it as one comma-separated editor under the Conversations rows. `message_wait_seconds` is labelled "Wait after any other text" and allows 0–60 (was 1–30). The migration is **0075** (renumbered at rebase: main's natural-replies 04 took 0074).
- Decisions: `?` is checked first, so "so?" reads finished; then trailing endings (so a long text ending in `...` trails, not finished); then last word / whole text in the list; then long + `.`/`!`/emoji. The last word is compared as typed (no punctuation stripping). An emoji is a "So" symbol at or after U+2600, past skin tones and joiners, so `°`/`™` don't count.
- Open question for Zaf (spec gap from the review): openers and trailing words share one list, as the issue says, so a single-word opener that ends a longer text also trails ("haha so funny lol", "it went fine anyway" wait 12s). If that feels slow in real chats, split into two lists (trailing words vs openers alone) or drop `lol`/`anyway`/`well`/`btw`/`omg`/`ugh` from the seed.

## Evidence

- Finished / trailing / neither, sticker, photo, Album, setting applies from the next text: `tests/test_message_wait.py` (31 webhook tests on `FakeTimer.waits`), incl. 15 words + `😂`, `❤️`, `👍🏽`, `...`, `…`, `,`, `BUT  `, `OK So  `, captionless photo, sticker alone, `30°` and `™` → neither.
- Start-over unchanged: existing `tests/test_messages.py` start-over tests pass; running app: "hey" then "rough day at work" sent while the reply was written → first reply dropped, one reply covering both, second wait 6.02s.
- Album: running app, 3 captionless Album photos → photos read ~12s after they arrived, one reply.
- Admin settings: `tests/test_admin_settings.py` (hints ≤ 2 sentences for every setting, seeded values, refusals for -1/61 seconds, 0/101 words, empty/blank/non-list words, trimmed + lower-cased save). Dashboard (`/run`, run-dashboard, 1280 and 390): all six fields show with hints in Conversations; 61 refused with "must be a whole number from 0 to 60"; trailing wait 9 and words "and, so, ok so, Honestly ," saved and reloaded as `and, so, ok so, honestly`.
- Applies from the next text (`/run`, load-test backend after that Dashboard save): "that was a lot honestly" waited 9.14s; "hmm" (taken out of the list) waited 6.46s.
- Migration: `tests/test_message_wait_migration.py` (15 → 6 with new defaults; Admin's 9 kept). `/run` through real backend start-up from 0074: 15 → 6 and the four new settings added; 9 kept; users and messages unchanged (6 users, 13 messages before and after).
- `/run` timing (worktree backend on load-test adapters, real `ThreadTimer`, real webhook; wait = Understanding start − Safeguard end): "what do you think I should do?" 2.06s, "so i was talking to my mum and" 12.04s, "ok so" 12.02s, "hey" 6.05s.
- Checks after rebase on main: `ruff check`, `ruff format --check`, `mypy` (222 files) clean; `pytest` 1613 passed; web `pnpm lint`, `format:check`, `typecheck` clean, `pnpm test` 902 passed.
- Docs: `docs/message-pipeline/README.md` decision 19 and step 2 note say built (except the cap, issue 02).

## Completion

- Completed: 2026-11-23
- Commit: d710295 (merge "Merge natural-replies-01-wait: the wait follows how the last text reads"; work in e4da08b "Natural replies 01: the wait follows how the last text reads", f8349fb review fixes, 7c23f07 migration renumbered to 0075, 0cd7e7e archive)
