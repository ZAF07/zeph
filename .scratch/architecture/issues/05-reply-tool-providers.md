# 05 — Give the reply tools one interface

Status: ready-for-agent

## Parent

Architecture review, 14 Nov 2026, point 4. Decided in a `/grill-with-docs` session.

## Why

`ResponseComposer` (`core/response_composition.py`) takes 9 dependencies and knows 6 tool shapes (web search, Settings in Chat, stickers, sticker adding, looking at photos again, sending a Shared Photo). Every new Feature tool widens the constructor and adds a special case to `compose`. Tests can only see what was offered by searching instruction strings.

## What to build

```python
class ReplyToolProvider(Protocol):
    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer: ...

@dataclass
class ReplyOffer:
    tools: list[ChatTool]
    instructions: str = ""
    picked: Attachment | None = None  # sticker or Shared Photo chosen during the reply
```

- The composer loops over a list of providers, wired in `main.py`. A new tool means a new provider, no composer edit.
- Each provider decides from the snapshot whether its Feature works; the composer does no Feature checks.
- The composer collects instructions and tools, and turns `picked` into the reply's sticker and Shared Photo.
- Tests assert on the offers, not instruction strings.

## Decisions

- Done now, before Understanding (`.scratch/understanding/`): this is the extension point Understanding will likely use (e.g. memory recall, Knowledge search, past patterns as tools the model chooses).
- No change in behaviour.

## Acceptance criteria

- [ ] `ReplyToolProvider` and `ReplyOffer`; the six existing tool sets are providers
- [ ] `ResponseComposer` constructor no longer lists each tool provider
- [ ] Tests per provider on the offer; composer test with fake providers
- [ ] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: a reply that uses web search, one that sends a sticker, and one that sends back a Shared Photo all work

## Blocked by

- `.scratch/architecture/issues/03-user-snapshot.md`

## Comments

### 14 Nov 2026 — plan (branch `arch-05-reply-tool-providers`)

- New `core/reply_tools.py`: `ReplyContext` (conversation ID, Shared Photo IDs), `ReplyOffer` (tools, instructions, `picked`), `Attachment` (sticker or Shared Photo) and the `ReplyToolProvider` protocol.
- Each of `WebSearchTools`, `SettingsTools`, `StickerTools`, `StickerAdding`, `PhotoTools`, `SendPhotoTools` gets `offer(snapshot, context) -> ReplyOffer`. `WebSearchOffer`, `SettingsOffer`, `StickerChoice`, `SendPhotoChoice` go; the pick tools set `offer.picked` instead.
- `ResponseComposer(repositories, chat_model, features, tool_providers)`. Order kept: providers listed in `app.py` (the wiring root; the issue says `main.py`) in today's order, so tools and instructions come out the same.
- Instructions order kept: memory, Knowledge, each offer's instructions, unavailable Features note, deletion-cancelled note.
- Tests: `tests/test_reply_tools.py` — composer with fake providers; one offer test per provider. Existing end-to-end tests stay as the "no behaviour change" check.
