# 16 — Knowledge is dropped when the Understanding names a document by its whole line

Status: completed

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

- [x] A document named by its whole listed line (quotes, source and tradition, with or without the "when it helps" part) is still found (`chosen_documents` and `comparable_name` in `src/companion/core/knowledge_retrieval.py`; also checked in the running stack, see Comments)
- [x] A test covers it at the webhook seam (scripted Understanding answer naming the document that way → passages reach the reply): `test_a_document_named_by_part_or_all_of_its_listed_line_is_found` in `tests/test_knowledge_when_it_helps.py`, 6 namings, red before the fix
- [x] The Knowledge eval uses the real-time `RunningClock`, and passes (`clock` fixture in `evals/test_knowledge_eval.py`): 8/8 in 4 of 6 runs; the 2 misses had the document found and passages in the reply (see Comments)
- [x] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` pass (930 passed)

## Comments

- 2026-11-14: Also shows in the Understanding Eval (issue 14), with only one document and the normal clock setup: `FAIL knowledge: chose “The Second Arrow” (Owner's notes, Buddhism), but no passage reached the reply` (`uv run pytest -n 0 evals -m eval -k knowledge-for-a-reflective-question`). Not every run, so the model does it some of the time, not only when the order changes.

### 2026-11-14 — fixed

What changed (branch `understanding-16-knowledge-whole-line`):

- `chosen_documents` now finds a document named by its title, its quoted title, `“title” (source, tradition)` or the whole listed line with "when it helps". Both sides are evened out first (`comparable_name`): straight quotes, single spaces, no leading "- " or trailing ":", any case.
- `KnowledgeDocument.title_with_source` writes the `“title” (source, tradition)` text in one place. The Understanding's document list, the reply's "From …" passages and the matching all use it.
- `evals/test_knowledge_eval.py` uses `RunningClock`, so documents get their own upload times and list newest first, as for real Users.

Checks: `ruff check`, `ruff format --check`, `mypy` (123 files) pass; `pytest` 930 passed.

Evals (real DeepSeek and fastembed):

- Knowledge eval with `RunningClock`, 6 runs: 8/8 in 4; 7/8 in 2. Before the fix it was 0/2 cases in 3 of 3 runs. With debug output on retrieval over 4 + 3 pebble runs, every whole-line name (e.g. `“The Windowsill Book” (Recorded by Elder Bramwell Osk, Fenmoor Hermits)`) was matched to its document and a passage reached the reply. The 2 misses were the reply not using the passage it was given (e.g. it named Elder Bramwell Osk but said it "cannot find" the rest), not this bug.
- Understanding eval, `knowledge-for-a-reflective-question`, 3 runs: all pass. One run named it `“The Second Arrow” (Owner's notes, Buddhism)`, another with straight quotes `"The Second Arrow" (Owner's notes, Buddhism)`; both found.

`/run` (worktree stack, `make db-copy` from main, 6 Ready documents, 84 chunks): ran the real `KnowledgeRetrieval.recall` inside the backend container on the real repositories, pgvector and fastembed, for the owner User. Named as `Mindful breathing`, `“Mindful breathing” (Owner’s summary, Mindfulness)`, `- “Mindful breathing” (…)` and `"Mindful breathing" (Owner's summary, Mindfulness)`: each gave two `From “Mindful breathing” (Owner’s summary, Mindfulness):` passages. `Not a document` gave no Knowledge. The webhook reply path wasn't used because a worktree's fake Telegram chat stops before the reply.

`/code-review`: Standards had no hard violations. Fixed: the title-with-source text built in three places; the `removeprefix` on both sides; the vague `named`; retrieval importing the Understanding module. Spec: fixed straight vs curly quotes, spacing, a trailing colon and the quoted title alone. Left as is: the `RunningClock` fixture is repeated in two evals (two short fixtures, each says why).

## Completion

- Completed: 2026-11-14
- Commits:
  - `cf98b3d` Understanding issue 16: find a Knowledge document named by its whole listed line
  - `23d03b0` Understanding issue 16 review fixes: even out quotes and spaces, one place for the title line
  - `b02deef` Understanding issue 16 done: archive issue with eval, run and review evidence; note reply-side Knowledge misses on issue 17
  - `f4654ab` Merge understanding issue 16: a Knowledge document is found when named by part or all of its listed line (into `main`)
