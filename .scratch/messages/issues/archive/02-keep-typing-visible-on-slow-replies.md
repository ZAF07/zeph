# 02 — Keep "typing" visible while a slow reply is written

Status: completed

## Parent

Split out of the Understanding grilling (`.scratch/understanding/issues/archive/01-understanding-before-reply.md`, 14 Nov 2026).

## What to build

Typing shows when the message arrives, but Telegram hides it after about 5 seconds. The steps before a reply (Safeguard, memory, Knowledge, the reply call, Web Search) can take longer, so the chat looks dead. While a reply is being worked on, show "typing" again every few seconds (Admin setting, start ~4 s) until the first part of the reply is sent. It stops on every path: reply sent, Crisis Reply, Limit Reply, deletion confirmed, or failure.

## Acceptance criteria

- [x] A reply that takes longer than the interval shows typing again at each interval until the first part is sent
- [x] Typing stops on every path, including failures (no typing after the "reply failed" message)
- [x] The interval is an Admin setting
- [x] Tests at the webhook seam with the fake clock and a slow scripted chat model; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: a slow reply in the worktree shows typing more than once (the recording chat channel shows repeated typing)

## Blocked by

None - can start immediately.

## Comments

### 14 Nov 2026 — implementation (branch `messages-02-keep-typing`)

Decisions:
- New core `TypingKeeper` (`src/companion/core/typing_keeper.py`) wraps the chat channel. `keep_up(chat_id, seconds)` shows typing again every N seconds using the existing `Timer` port (key `typing:<chat_id>`). Any text, sticker or photo sent to that chat, or `stop()`, ends it. A per-chat lock makes a send wait for typing being shown right now, so typing can't land after the message.
- `create_app` wraps the chat channel once, so every sender stops typing — reply, Crisis Reply, Limit Reply, deletion confirmed, failure message — without each path knowing.
- `IncomingMessageHandler` starts it inside the turn lock before a text is screened (covers a slow Safeguard and the Message wait) and when a Message is answered (covers Albums); stops it in `finally` once the answer ends.
- Admin setting `typing_repeat_seconds` (seed 4, range 1–5, since Telegram hides typing after ~5 s); Dashboard field "Typing repeat" in Platform settings → Conversations. Loaded from the seed on start, no migration.

Tests: `tests/test_typing.py` (7 tests, webhook seam, FakeTimer `end_typing_waits()` run while the scripted model is "slow"). Red with the handler/app wiring stashed (7 failed), green with it.

`/run` (worktree stack, inside the backend container; real repositories, real `ThreadTimer` and clock, real core services; only chat channel swapped for a recording one and the chat model for an 11 s slow scripted one — Telegram can't reach a fake chat, see memory note):

Slow reply:
```
  4.2s  User sends 'hey'
  4.5s  typing
  8.4s  typing
  8.9s  reply call starts (will take 11s)
 12.4s  typing
 16.4s  typing
 20.0s  typing            <- deliver_reply's own typing pause
 20.4s  typing
 21.5s  text: 'sorry, that took a while!'
 (nothing more over the next ~10 s)
```
Failing reply:
```
  0.9s  typing
  4.9s  typing
  5.0s  reply call starts (will take 11s)
  8.9s  typing
 12.9s  typing
 16.0s  text: 'Sorry, my thoughts got tangled ... Could you send that again?'
 (nothing more over the next ~18 s)
```

### 14 Nov 2026 — code review

Standards: no hard violations. Spec: matches the issue; every path ends in a send or `stop`.

Fixed:
- No test for a failed text check or for Albums → added `test_typing_stops_when_a_text_fails_to_be_checked` and `test_typing_shows_again_while_an_album_is_answered`.
- One failed `show_typing` call ended the repeats for that Message → `_show_again` now logs the error and still schedules the next try (`test_one_failed_typing_call_does_not_end_the_typing_repeats`, red before the fix).
- `FakeTimer.end_typing_waits` copied `end_message_waits` → shared `_end_waits(prefix)`.

Kept on purpose:
- `TypingKeeper` passes most calls straight through (Middle Man). It is a decorator over the `ChatChannel` port, and that is why every sender stops typing on its own.
- Every service gets the wrapped channel, so no sender (e.g. an Admin's sticker-adding notice) can leave typing showing after its message. A side effect: a notice sent mid-reply also ends that reply's typing repeats. That is fine, because something did arrive.
- `IncomingMessageHandler` gets the same object as `chat_channel` and `typing_keeper`. The two roles stay readable at each call site.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - Typing shows again at each interval until the first part: `test_a_slow_reply_shows_typing_again_at_each_interval_until_the_first_part`, `test_typing_shows_again_while_a_text_is_slow_to_check_and_while_waiting`, `test_typing_shows_again_while_an_album_is_answered`; `/run` shows typing every ~4 s through an 11 s reply call.
  - Stops on every path: `test_typing_stops_when_the_crisis_reply_is_sent`, `..._the_limit_reply_is_sent`, `..._deleting_data_is_confirmed`, `..._the_reply_fails`, `..._a_text_fails_to_be_checked`; plus the slow-reply test. Each one ends any typing wait left and checks no typing follows. `/run` failure mode shows no typing for 18 s after the "reply failed" message.
  - Admin setting: `typing_repeat_seconds` (seed 4, editable 1–5, `EditableSetting` "Typing repeat"; Dashboard field in Platform settings → Conversations); `test_the_interval_is_the_admins_typing_repeat_setting` and the PlatformSettingsForm test.
  - Tests and checks: pytest 777 passed; ruff, ruff format --check, mypy clean; web lint, format:check, typecheck, test (343 passed), build OK.
  - `/run`: see the Comments above (run twice, the second time on the final code after review).
- Commits: `2f1741d` (implementation), `32b60d5` (review fixes), merged to main in `d1e16fb` ("Merge messages issue 02: keep typing visible while a slow reply is written …").
- Archived in `dec2c0c` (rename only; the completion edits landed in the next commit, "Messages issue 02: mark completed with evidence and commits").
