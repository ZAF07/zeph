# 06 — Typed platform settings, read once

Status: ready-for-agent

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

- [ ] Every setting read goes through a typed key; no string-key `get` calls remain
- [ ] One settings query per reply and per tick (test)
- [ ] mypy catches a wrong key or type
- [ ] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: an Admin edits the Persona; the next reply uses it

## Blocked by

None. Fits well with issue 03 (loaded at the same points as the `UserSnapshot`).
