# 05 — Give the reply tools one interface

Status: completed

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

- [x] `ReplyToolProvider` and `ReplyOffer`; the six existing tool sets are providers
- [x] `ResponseComposer` constructor no longer lists each tool provider
- [x] Tests per provider on the offer; composer test with fake providers
- [x] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: a reply that uses web search, one that sends a sticker, and one that sends back a Shared Photo all work

## Blocked by

- `.scratch/architecture/issues/03-user-snapshot.md`

## Comments

### 14 Nov 2026 — plan (branch `arch-05-reply-tool-providers`)

- New `core/reply_tools.py`: `ReplyContext` (conversation ID, Shared Photo IDs), `ReplyOffer` (tools, instructions, `picked`), `Attachment` (sticker or Shared Photo) and the `ReplyToolProvider` protocol.
- Each of `WebSearchTools`, `SettingsTools`, `StickerTools`, `StickerAdding`, `PhotoTools`, `SendPhotoTools` gets `offer(snapshot, context) -> ReplyOffer`. `WebSearchOffer`, `SettingsOffer`, `StickerChoice`, `SendPhotoChoice` go; the pick tools set `offer.picked` instead.
- `ResponseComposer(repositories, chat_model, features, tool_providers)`. Order kept: providers listed in `app.py` (the wiring root; the issue says `main.py`) in today's order, so tools and instructions come out the same.
- Instructions order kept: memory, Knowledge, each offer's instructions, unavailable Features note, deletion-cancelled note.
- Tests: `tests/test_reply_tools.py` — composer with fake providers; one offer test per provider. Existing end-to-end tests stay as the "no behaviour change" check.

### 14 Nov 2026 — done (pending merge)

- Built test-first: `tests/test_reply_tools.py` failed first (no `companion.core.reply_tools`), then passed.
- `core/reply_tools.py` holds `ReplyContext`, `ReplyOffer`, `Attachment` and `ReplyToolProvider`. `WebSearchOffer`, `SettingsOffer`, `StickerChoice` and `SendPhotoChoice` are gone. The pick tools (`sticker_offer`, `send_photo_offer`) set `offer.picked`. `StickerAdding.tools(user)` is now `offer(snapshot, context)`.
- `ResponseComposer(repositories, chat_model, features, tool_providers)`. The providers are listed in `app.py`, the wiring root (the issue says `main.py`), in the old order, so the tools and instructions come out the same.
- Code review (Standards and Spec run in parallel): no defects, no behaviour change. Fixed: empty offers are now written `ReplyOffer()`, and the test pick tool has a docstring. Not changed: `sticker_offer` and `send_photo_offer` share a shape (the same was true before the change); if two providers ever picked the same kind of item, the last pick would win (today only one provider picks each kind).
- `/run` (worktree Postgres on 5562, real DeepSeek and Tavily): the production adapters, with only the chat channel swapped for one that records, since Telegram can't reach a made-up chat. Setup: a seeded onboarded User, two noted library stickers and one Shared Photo (Miso the cat).
  - "Can you look up the latest news about the James Webb telescope this week?" → Tavily search "James Webb Space Telescope news this week", and the reply named the Lion Nebula and Treasure Chest results.
  - "I FINALLY ran my first 5k today!! Send me a celebration sticker 🎉" → "How did it feel out there?" then `sticker: run-sticker-party`.
  - "I miss Miso so much today. Can you send me that photo of her again?" → "That windowsill patch of sun was made for her." then `photo: run-photo-miso`.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - `ReplyToolProvider`, `ReplyOffer` (`src/companion/core/reply_tools.py`); the six providers each have `offer(snapshot, context) -> ReplyOffer`: `web_search.py:69`, `chat_settings.py:514`, `stickers.py:297`, `sticker_adding.py:177`, `photos.py:490` (look again), `photos.py:625` (send photo).
  - `ResponseComposer.__init__` takes one `tool_providers` list (`response_composition.py:88`), wired in `app.py:217`.
  - `tests/test_reply_tools.py`: 3 composer tests with fake providers (tools and instructions in order, the context passed, picks become the sticker or Shared Photo, empty reply), 6 offer tests (one per provider).
  - `pytest` 628 passed (619 before, plus 9 new; 9 evals deselected); `ruff check .` clean; `ruff format --check` clean on code; `mypy` no issues in 101 files.
  - `/run`: web search, sticker and Shared Photo replies all worked in the real app, see Comments.
- Commits: 60f1ff3 "Give the reply tools one interface", ffd9696 "Review fixes: write empty offers as ReplyOffer(), docstring the test pick tool", archive 92ad558 "Architecture issue 05 done: archive issue with test, run and review evidence" (merged from `arch-05-reply-tool-providers` in 365fe56 "Merge architecture issue 05: give the reply tools one interface")
- Checks on main after the merge: `pytest` 628 passed, `ruff check`, `ruff format --check` and `mypy` clean.
