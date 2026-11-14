# 02 — Keep "typing" visible while a slow reply is written

Status: ready-for-agent

## Parent

Split out of the Understanding grilling (`.scratch/understanding/issues/01-understanding-before-reply.md`, 14 Nov 2026).

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
