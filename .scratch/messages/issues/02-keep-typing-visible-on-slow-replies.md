# 02 — Keep "typing" visible while a slow reply is written

Status: in-progress

## Parent

Split out of the Understanding grilling (`.scratch/understanding/issues/archive/01-understanding-before-reply.md`, 14 Nov 2026).

## What to build

Typing shows when the message arrives, but Telegram hides it after about 5 seconds. The steps before a reply (Safeguard, memory, Knowledge, the reply call, Web Search) can take longer, so the chat looks dead. While a reply is being worked on, show "typing" again every few seconds (Admin setting, start ~4 s) until the first part of the reply is sent. It stops on every path: reply sent, Crisis Reply, Limit Reply, deletion confirmed, or failure.

## Acceptance criteria

- [ ] A reply that takes longer than the interval shows typing again at each interval until the first part is sent
- [ ] Typing stops on every path, including failures (no typing after the "reply failed" message)
- [ ] The interval is an Admin setting
- [ ] Tests at the webhook seam with the fake clock and a slow scripted chat model; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: a slow reply in the worktree shows typing more than once (the recording chat channel shows repeated typing)

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
