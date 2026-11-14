# 16 — Knowledge is dropped when the Understanding names a document by its whole line

Status: ready-for-agent

## Symptom

The Understanding call sees each Knowledge document as a line like:

```
- “The Lantern Breath” (Notes of Teacher Orsolya Vey, Haldric Stoicism): When someone is lying awake…
```

Sometimes DeepSeek copies that line instead of just the title:

```json
"knowledge": {"documents": ["“The Lantern Breath” (Notes of Teacher Orsolya Vey, Haldric Stoicism)"], "search": "…"}
```

Titles must match exactly (ignoring case), so the document isn't found, no passages are searched and the reply gets no Knowledge. Expected: the reply gets passages from The Lantern Breath. Nothing crashes and nothing is logged. The reply just makes the practice up (in the eval it invented a 4-2-6 breath with a "warm light" instead of the document's seven counts and blue lantern).

It happens when documents have different upload times, which puts the newest first in the list. With the evals' frozen `FakeClock`, every document has the same upload time and they list in title order, which hid this. Real Users always have documents uploaded at different times, so this can happen in production.

Found 2026-11-14 while building issue 14 (Understanding Eval).

## Repro

Deterministic in 3 of 3 runs (and passes 3 of 3 with the frozen clock):

1. In `evals/conftest.py`, change the `clock` fixture to return `RunningClock(datetime.now(UTC))` (from `evals/running_clock.py`).
2. `set -a && . ./.env && set +a && uv run pytest -n 0 evals -m eval -k knowledge_eval`
3. Both Knowledge cases fail with "uses no version". The Model Call Log content for the Understanding call shows the document named by its whole line.

## Suspected location

`chosen_documents` in `src/companion/core/knowledge_retrieval.py` (exact title match). The line format is written by `format_knowledge_document` in `src/companion/core/understanding.py`.

## Acceptance criteria

- [ ] A document named by its whole listed line (quotes, source and tradition, with or without the "when it helps" part) is still found
- [ ] A test covers it at the webhook seam (scripted Understanding answer naming the document that way → passages reach the reply)
- [ ] The Knowledge eval uses the real-time `RunningClock`, and passes
- [ ] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` pass

## Comments

- 2026-11-14: Also shows in the Understanding Eval (issue 14), with only one document and the normal clock setup: `FAIL knowledge: chose “The Second Arrow” (Owner's notes, Buddhism), but no passage reached the reply` (`uv run pytest -n 0 evals -m eval -k knowledge-for-a-reflective-question`). Not every run, so the model does it some of the time, not only when the order changes.
