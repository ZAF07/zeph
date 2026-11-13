# 28 — The Telegram bot token shows up in backend logs

Status: completed

## Parent

`.scratch/mvp/PRD.md` (seen during the `/run` for `issues/archive/14-data-retention-and-deletion.md`)

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

## Decisions (from `/grill-with-docs`, 2026-11-13)

- **Fix it in the Telegram adapter only, with no global log filter.** Only Telegram puts a secret in a URL. Tavily and Clerk send keys in the `Authorization` header and DeepSeek wraps its key in `SecretStr`, and httpx errors don't show headers. A filter would only match the patterns we thought of. No Telegram error text is saved to the DB or shown on the Dashboard, so logs are the only place it leaks.
- **Also pin the `httpx` and `httpcore` loggers to WARNING at backend startup.** httpx logs every request URL at INFO. Today that's hidden only because nothing sets up logging, so raising the log level later would print the token on every call.
- **Rotate only when there's a reason, not on a schedule:** the token leaked or might have, or someone who had it no longer should. Telegram tokens never expire. The steps are in `docs/RESET_TELEGRAM_TOKEN_GUIDE.md`, and issue 16 links to it.
- **Rotate the current token only after the fix is running.** If you rotate first, the next failed call leaks the new token too.
- No ADR or `CONTEXT.md` change: this is easy to undo and adds no domain terms.

## What to build

In `chat_channel.py`, catch `httpx.HTTPError` in `_call` and the file download and raise our own Telegram error instead. Its message holds the Bot API method name, the status code and Telegram's `description` from the response body, never the URL. Raise it `from None` so the original httpx error, URL included, isn't printed as its cause. The error keeps the status code as an attribute, because the sticker-set lookup (`except httpx.HTTPStatusError` around `getStickerSet`) treats 400 as "no such set". Update that catch and the `httpx.HTTPError` lines in the docstrings' `Raises:` sections. Connection errors (`httpx.RequestError`) get the same wrapping.

## Acceptance criteria

- [x] A failed Telegram call or file download raises our own Telegram error whose message has the method name, status code and Telegram's `description`, and never the token; the httpx error is not chained (`from None`)
- [x] A test fails a Telegram call through a fake httpx transport and checks the token appears nowhere in the error text or the logged traceback
- [x] At startup the backend sets the `httpx` and `httpcore` loggers to WARNING, with a test
- [x] `/run`: a reply that fails (chat ID that doesn't exist) leaves no `api.telegram.org/bot` in `docker compose logs backend`
- [x] `docs/RESET_TELEGRAM_TOKEN_GUIDE.md` gives Admins the steps to reset the token, and issue 16 links to it (written during the grilling)
- [ ] **(User, after merge and deploy)** Rotate the current token by following the guide

## Comments

Implementation (2026-11-13): `TelegramApiError` in `src/companion/adapters/telegram/chat_channel.py` replaces every httpx error leaving `_call` and `_download`, raised `from None`. Its message is "Telegram <method> failed with status <code>: <description>" (or "could not be reached: <ErrorType>" for connection errors) and it keeps `status_code` for the sticker-set 400 check. `quiet_http_client_logs()` in `src/companion/main.py` runs first in `build_production_app`.

Evidence:
- Error text and no chaining: `tests/adapters/test_telegram_chat_channel.py` — `test_a_refused_photo_raises` (exact message, status 400), `test_a_refused_file_download_raises_without_the_token`, `test_an_unreachable_telegram_raises_without_the_token`, `test_an_unknown_sticker_set_is_none` (400 still means "no such set").
- Token absent from the logged traceback: `test_a_refused_call_leaves_the_token_out_of_the_logged_traceback` (caplog has no `123:abc` and no `api.telegram.org/bot`; `__cause__` is None and context suppressed).
- Logger pinning: `tests/test_config.py::test_http_client_loggers_are_pinned_to_warning`.
- `/run` (worktree stack, backend on 8050): posted a webhook update from chat ID 1. The backend log shows `TelegramApiError: Telegram sendMessage failed with status 400: Bad Request: chat not found`, and `docker compose logs backend | grep -c api.telegram.org/bot` gives 0.
- Checks: `uv run pytest` 508 passed, 9 deselected; `ruff check`, `ruff format --check` and `mypy src` all clean. No web changes.
- `/code-review`: no Standards violations and no Spec findings. Applied the optional points: clearer helper names (`to_telegram_api_error`, `telegram_error_description`) and `pytest.raises` in the traceback test.

Still open (User step, after merge and deploy): rotate the current token by following `docs/RESET_TELEGRAM_TOKEN_GUIDE.md`. The fix must be running first, otherwise the next failed call leaks the new token too.

## Completion

- Completed: 2026-11-13
- Commit: 813439c "Issue 28: Telegram errors no longer carry the bot token", review fixes 45477bb "Issue 28: clearer helper names and pytest.raises in the traceback test (review)", archive d368fdc "MVP issue 28 done: archive issue with test, run and review evidence" on branch `mvp-28-telegram-token-logs` (merged into main in d30b9fa "Merge MVP issue 28: failed Telegram calls and file downloads now raise TelegramApiError with the method, status code and Telegram's description instead of an httpx error whose URL held the bot token…")
