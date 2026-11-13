# 28 — The Telegram bot token shows up in backend logs

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (seen during the `/run` for `issues/archive/14-data-retention-and-deletion.md`)

## Before deciding on a solution

Run `/grill-with-docs` on this issue first. The user wants to grill the problem with the docs before a solution is picked, so don't start on a fix until that is done.

## Symptom

Telegram puts the bot token inside the request URL (`https://api.telegram.org/bot<TOKEN>/sendMessage`). When Telegram refuses a call, httpx raises `HTTPStatusError`, whose message holds the full URL. Our code logs that error with its traceback (e.g. `logger.exception` in `core/incoming_messages.py`), so the token is written to the backend logs in plain text:

```
httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://api.telegram.org/bot<TOKEN>/sendMessage'
```

Normal successful calls don't log the URL. Only failed Telegram calls do.

Impact: anyone who can read the backend logs (or anything the logs are copied to) can take the token and control the bot: read what Users send and send messages as Zeph. The token already appeared in a Claude Code session transcript this way, so it should be rotated whatever fix is picked.

## Repro

Deterministic. With the stack running, make any Telegram call fail, e.g. send a reply to a chat ID that doesn't exist. Then check `docker compose logs backend` for `api.telegram.org/bot`.

## Suspected location

- `src/companion/adapters/telegram/chat_channel.py` — the token is built into `_bot_url` and `_file_url`, and httpx errors leave the adapter as they are.

## Questions for the grilling

- Fix it in the Telegram adapter only (re-raise errors with the token masked), or add a log filter that masks secrets for every adapter?
- Do other adapters put secrets in URLs or error messages (DeepSeek, Tavily, Clerk)?
- Should httpx's own request logging be switched off or kept at WARNING on purpose, so a future log-level change doesn't start printing every URL?
- Is rotating the token a one-off step, or should rotation be written down (e.g. in the deployment docs for issue 16)?

## Acceptance criteria

To be written after `/grill-with-docs`.

## Comments
