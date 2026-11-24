# 04 — Photos through OpenRouter

Status: ready-for-agent
Blocked by: 02, 03

## Parent

`.scratch/openrouter/PRD.md` (user stories 15, 21).

## What to build

An OpenRouter adapter behind the `PhotoViewer` port. It sends the instructions as a system message and the photo as an image data URL in a user message, with thinking and the model name handled as in 02. It returns the text, tokens and reasoning. With `openrouter` as the adapter, photo viewing uses it. Once this and 03 are done, every model call works through OpenRouter, so this slice makes `openrouter` the default `CHAT_MODEL_ADAPTER`, with `deepseek` kept as the backup.

## Acceptance criteria

- [ ] Adapter tests: photo sent as a data URL with its media type; model name and thinking sent as given; text and tokens returned
- [ ] Adapter choice builds the OpenRouter photo viewer for `openrouter`, and `openrouter` is now the default (tests)
- [ ] `/run`: with the default adapter, a plain reply, a tool reply and a photo reply all work; switching to `deepseek` still works
- [ ] Contract test (remind the operator first): a photo is described through OpenRouter
- [ ] `/run`: a photo posted through the Telegram webhook is looked at, and the Model Call Log shows the photo model call
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02
- 03

## Comments
