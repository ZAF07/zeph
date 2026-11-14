# 06 — Typed platform settings, read once

Status: completed

## Parent

Architecture review, 14 Nov 2026, point 5. Decided in a `/grill-with-docs` session.

## Why

About 84 `settings.get("key")` calls across the backend. Each uses a bare string key (a typo only shows up at runtime), returns `Any` (mypy can't check it), and is its own DB query (about 15 per reply). Must scale.

## What to build

- Typed keys declared once, next to `EDITABLE_SETTINGS` in `core/platform_settings.py`, e.g. `PERSONA = Setting[str]("persona")`.
- Settings are loaded in one query per reply and per Check-in tick (and per Dashboard request where used); `settings.get(PERSONA)` returns a `str`.
- Parsing (JSON shapes, e.g. hours between Check-ins per frequency) happens once, in the typed key, and is tested once.
- Callers stop using string keys.

## Decisions

- Typed keys plus read once, not one big `PlatformSettings` dataclass: a new setting is one line, and it scales (1 query instead of about 15).
- ADR-0004 unchanged: Admins still manage the values; only the reading side gets typed.
- A settings change made mid-reply is seen from the next reply on.

## Acceptance criteria

- [x] Every setting read goes through a typed key; no string-key `get` calls remain
- [x] One settings query per reply and per tick (test)
- [x] mypy catches a wrong key or type
- [x] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: an Admin edits the Persona; the next reply uses it

## Blocked by

None. Fits well with issue 03 (loaded at the same points as the `UserSnapshot`).

## Comments

### 14 Nov 2026 — plan (branch `arch-06-typed-settings`)

- `core/models.py`: `Setting[T]` (key + a `read` function that turns the stored value into `T`) and `PlatformSettings` (the values read once; `get(setting) -> T`). In `models.py` so `ports.py` and `UserSnapshot` can name them without a circular import.
- `core/platform_settings.py`: every typed key, e.g. `PERSONA = Setting("persona", read_text)`, plus the small `read_*` functions (text, whole number, number, minutes, hours, text list, hours between Check-ins per frequency). `EditableSetting` takes the typed key, so each key string is written once. The placeholders (`{helplines}`, `{features}`, `{dashboard_url}`) move here too, which breaks the import loop.
- Port: `PlatformSettingsRepository.get(key)` is replaced by `load() -> PlatformSettings` (one query, every row). `get_many` / `save_many` stay for the Admin page.
- Reply: `IncomingMessageHandler._answer` loads settings once and passes them to `UserSnapshotLoader.load`; the snapshot carries them as `snapshot.settings`, so every reply step and reply tool reads the same values. `deliver_reply` takes the settings too (typing pause).
- Tick: `ScheduledWork.tick` loads settings once and hands them to post-conversation, Check-ins (and `load_many`) and message retention.
- Dashboard / other paths (Telegram connect, home, usage report, Check-ins page, memory categories): one `load()` per call.
- `timing.quiet_gap` / `check_in_reply_window` go away: the typed keys read straight to a `timedelta`.
- Tests: a reply and a tick each read `platform_settings` once; every typed key reads its seeded value; the `read_*` functions reject a wrong shape.

### 14 Nov 2026 — done (pending merge)

- Built test-first: `tests/test_platform_settings_reads.py` was red before the change (one reply read `platform_settings` 24 times, one tick with 3 due Users and an ended Conversation 23 times), then green at 1 and 1.
- Decision: the reply's settings ride on the snapshot as `UserSnapshot.settings`, instead of a second argument next to the snapshot through every step and reply tool. This changes issue 03's "Not in the snapshot: platform settings": the snapshot is now "what a reply or tick read once when it started". The loader doesn't read settings itself; `load` / `find` / `load_many` take them, so a tick's one read is shared by post-conversation, every Check-in snapshot and message retention.
- `EditableSetting` keeps `key: str`, filled from the typed key (`PERSONA.key`), so each key string is still written once. The placeholders moved into `platform_settings.py` to break an import loop.
- `timing.quiet_gap` and `timing.check_in_reply_window` are gone: `CONVERSATION_QUIET_GAP` and `CHECK_IN_REPLY_WINDOW` read straight to a `timedelta`, and `CHECK_IN_GAPS` to a gap per frequency.
- Dashboard: Home reads settings once per request (it was 4: Goals category, last Check-in, memory note, AI notice). Other one-off paths (Telegram connect, usage report, Check-ins page, memory categories, sticker adding) do one `load()` each.
- Left as is on purpose: while an album collects, each photo's webhook request reads settings once for the wait time; the reply itself still reads once. `PlatformSettings.get` runs the key's read function on each call; the rule is written once, and the values are tiny.
- mypy check (a throwaway file run with `mypy --strict`): `settings.get("persona")` → `incompatible type "str"; expected "Setting[Never]"`; `x: int = settings.get(PERSONA)` → `expression has type "str", variable has type "int"`; `minutes: int = settings.get(CONVERSATION_QUIET_GAP)` → `has type "timedelta"`; a misspelt key → `Name "PERSONNA" is not defined`. During the change, mypy flagged every leftover string-key read (27 errors) until each was moved to a typed key.
- Code review (Standards and Spec in parallel). Fixed: a stray `settings` line in the `_save` docstring; `incoming_messages` uses `DASHBOARD_URL_PLACEHOLDER` instead of the raw string. Not changed: keys stay in `platform_settings.py` (the issue puts them next to `EDITABLE_SETTINGS`); the daily-limit check reads each snapshot's own settings (no extra argument); the album and parse-on-get points above.
- `/run` (worktree stack, ports 3130/8130/5562, real DeepSeek):
  - Signed in to the Dashboard as an Admin (Clerk test user) and, on `/admin/persona`, added "Run check: end every message you send with the exact word Marmalade." and pressed Save Persona. The page showed "Saved. Zeph uses it from the next message." and "Last saved 14 Nov, 13:18 by Run check".
  - Then answered one Telegram message ("hey, just finished a long run by the river") for a seeded connected User through `build_production_app()`, with only the chat channel swapped for one that records (Telegram can't reach a fake chat) and the scheduler stopped. Reply: "That sounds like a good way to end a day. River air is different somehow, cooler and a bit green." / "How far did you go? Marmalade". Reads of `platform_settings` during the reply: 1.
  - The Docker backend (new code, its scheduler ticking) logged no errors; Dashboard Home and `/api/platform-content` answered 200.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - No string-key reads: `grep -rnE "settings\.get\(\s*[\"']|platform_settings\.get\(" src scripts evals` finds only typed-key reads; the port's `get(key)` is gone (`PlatformSettingsRepository.load()`).
  - One read per reply and per tick: `test_a_reply_reads_the_platform_settings_once`, `test_a_tick_reads_the_platform_settings_once`. Typed keys: `tests/test_setting_keys.py` (every seeded setting has one typed key that reads it; wrong shapes fail).
  - mypy catches a wrong key or type: see the mypy check in Comments.
  - `pytest` 704 passed (9 deselected evals), `ruff check` and `ruff format --check` clean, `mypy` no issues in 103 files.
  - `/run`: Admin edited the Persona on the Dashboard; the next reply followed it (see Comments).
- Commits:
  - 8b8e584 "Read typed platform settings once per reply, tick and request"
  - 2c5f2e9 "Review fixes: drop stray settings arg from _save docstring, use the dashboard_url placeholder"
  - 24588f7 "Architecture issue 06 done: archive issue with test, run and review evidence"
  - 0b6ec07 "Glossary: Platform Settings"
  - 17aed00 "Architecture issue 06: record commits in the archived issue"
  - 1634a1c "Merge architecture issue 06: typed platform settings, read once" (merged from `arch-06-typed-settings` into main)
