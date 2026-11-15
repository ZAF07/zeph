# 19 — The Understanding picks Knowledge documents by number, not by copying titles

Status: completed

## What

The Understanding sees each Ready Knowledge document as a listed line and answers with the titles of the ones worth searching (`"knowledge": {"documents": ["<document title>"], …}`). Because it has to copy a title back as text, it sometimes copies more or less than the title. Bug 16 fixed this by accepting the forms seen so far (the whole line, the title with source, straight quotes, extra spaces). Any form we haven't seen, like the title with only the source, is still dropped quietly, and the reply makes the practice up.

Number the documents in the list the Understanding reads, and have it answer with the numbers:

```
Knowledge documents, with when each helps:
[1] “The Lantern Breath” (Notes of Teacher Orsolya Vey, Haldric Stoicism): When someone is lying awake…
[2] “Mindful breathing” (Owner’s summary, Mindfulness): …
```

```json
"knowledge": {"documents": [1], "search": "…"}
```

A number that's not in the list is ignored. The numbers only hold for one Understanding call, so the call must keep its own number-to-document map (the list can change between calls).

## Where

- List format: `format_knowledge_document` and `describe_message_for_understanding` in `src/companion/core/understanding.py`.
- Reading the answer: `read_knowledge_lookup` in `src/companion/core/understanding.py`, and `KnowledgeLookup` in `src/companion/core/models.py` (holds titles today).
- Matching: `chosen_documents`, `comparable_name`, `comparable_names_for` in `src/companion/core/knowledge_retrieval.py`. With numbers this name matching can go.
- Prompt: `understanding_prompt` in `src/companion/seed/platform_settings.yaml` (the `knowledge:` bullet says "titles exactly as written", and the JSON shape). The seeded wording reaches existing installs only through a migration (latest: `0036_understanding_shape.py`).
- The saved Understanding keeps its `KnowledgeLookup`, and the Model Call Log (full content) shows the raw answer. With numbers, the raw answer only says `[1]`, so the saved Understanding should keep the chosen documents' titles (or IDs), not the numbers. The Understanding eval reads the chosen names from it (`evals/test_understanding_eval.py`, `form.knowledge.documents`).

## Acceptance criteria

- [x] The Understanding reads numbered Knowledge documents and answers with numbers; the chosen documents' passages reach the reply (`number_knowledge_documents`, `format_knowledge_document` and `read_knowledge_lookup` in `src/companion/core/understanding.py`; retrieval matches by ID in `chosen_documents`, `src/companion/core/knowledge_retrieval.py`; seen live, see Comments)
- [x] A number not in the list, or a title instead of a number, picks nothing and doesn't crash (2, 0, -1, true, "1", a title, the title with source, an object: all give no Knowledge, a saved `knowledge: null` and a normal reply)
- [x] Tests at the webhook seam cover both: `test_the_understanding_picks_documents_by_their_listed_number` and `test_a_number_not_in_the_list_or_a_title_picks_nothing` (8 cases) in `tests/test_knowledge_when_it_helps.py`, red before the change
- [x] The seeded Understanding prompt is updated, with a migration for existing installs (`understanding_prompt` in `src/companion/seed/platform_settings.yaml`; `0037_knowledge_by_number.py`; `test_an_existing_install_gets_the_prompt_that_picks_knowledge_by_number`, red without the migration)
- [x] The saved Understanding records which documents were chosen by title or ID, not by list number (`ChosenKnowledgeDocument(document_id, title)` in `src/companion/core/models.py`; saved and loaded in `src/companion/adapters/postgres/repositories.py`; the Understanding eval reads `.title`)
- [x] The Knowledge eval (with `RunningClock`) and the Understanding eval's Knowledge cases pass at least as often as after bug 16 (Knowledge eval 8/8 in 6 of 6 runs, vs 4 of 6 after bug 16; Understanding Knowledge checks 7 of 7 runs, see Comments)
- [x] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` pass (mypy 124 files; pytest 935 passed)

## Blocked by

- `.scratch/understanding/issues/archive/16-knowledge-dropped-when-document-named-by-its-whole-line.md` (done)

## Comments

- 2026-11-15: Raised after bug 16. Picking from a fixed set means there's nothing to copy wrong. Another option is to make the answer's format allow only the listed titles (a JSON schema enum); numbers were chosen because they also work with models and providers that don't enforce schemas.
- 2026-11-15: Done.
  - The Understanding sees `[n] “title” (source, tradition): when it helps` and answers `"knowledge": {"documents": [n], "search": "…"}`. Each call numbers the Ready documents itself (`number_knowledge_documents`) and reads the answer with that same map, so a list that changes between calls can't mix numbers up.
  - The saved Understanding keeps `{"document_id", "title"}` per chosen document. Retrieval searches the chosen IDs that are still Ready. `comparable_name` and `comparable_names_for` from bug 16 are gone.
  - Saved forms from before this change named documents by title only. Loading them skips those names instead of failing, so a Conversation already going when this ships still works.
  - `read_number` is now the one check for "a whole number, not true/false or text", used by Life Threads, Curiosities and Knowledge.
  - Migration 0037 deletes the saved `understanding_prompt` so it reloads from the seed, as 0033 did. An Admin's own edits to that prompt are replaced too.

  Checks: `ruff check`, `ruff format --check`, `mypy` (124 files) pass; `pytest` 935 passed. No Dashboard files changed.

  Evals (real DeepSeek and fastembed, settings from the seed file):
  - Knowledge eval with `RunningClock`, 6 runs: 8/8 in all 6. After bug 16 it was 8/8 in 4 of 6.
  - Understanding eval, `knowledge-for-a-reflective-question`, 3 runs: all pass ("chose The Second Arrow; passages from The Second Arrow reached the reply").
  - `no-knowledge-for-a-vent`, 7 runs on this branch: the Knowledge check passed every time ("chose no document"). The case failed 3 times on the `no_teaching` reply rule (the judge read lines like "I know how you'll be with it" as teaching). On main the same case failed 1 of 4 runs the same way, and this branch failed 1 of 4 when run alone. That's the reply judge being flaky, not this change.

  `/run` (worktree stack, `make db-copy` from main, 6 Ready documents; migration 0037 ran on start): sent real messages through the whole webhook path (`create_app` with the real repositories, DeepSeek, fastembed and pgvector) inside a backend container for the owner. Only Telegram (printing channel), the timer and the scheduler were swapped, because a worktree's fake Telegram chat stops before the reply.
  - "I keep getting lost in my head tonight. Can you walk me through the mindful breathing practice?": the Understanding saw `[1] “Self-compassion” …` through `[6] “Dhammapada (selections)” …` and answered `"documents": [3]` (`[3] “Mindful breathing”`). The reply got two `From “Mindful breathing” (Owner’s summary, Mindfulness):` passages and walked through the practice. Saved: `{"documents": [{"document_id": "b9f8e43a-…", "title": "Mindful breathing"}], "search": "mindful breathing practice step by step"}`.
  - A follow-up vent in the same Conversation (so the saved form above was loaded back): `"knowledge": null`, no passages, and a normal reply.

  `/code-review`: Standards found no hard violations. Fixed: the number check was now copied three times (it's now `read_number`), and `ChosenKnowledgeDocument` is built with keyword arguments. Left as is: the plain number→document map (simpler than a new type), and passing reminded Threads, due Curiosities and Knowledge documents separately (bundling them is a wider refactor). Spec found nothing missing. Fixed a stale eval docstring ("as it named them").

## Completion

- Completed: 2026-11-15
- Commits:
  - `dc1f5e1` Understanding issue 19: pick Knowledge documents by number
  - `422d977` Understanding issue 19 review fixes: one number reader for Threads, Curiosities and Knowledge
  - `fc74f0b` Understanding issue 19 done: archive issue with eval, run and review evidence
  - `8200f14` Merge understanding issue 19: the Understanding picks Knowledge documents by their number in a numbered list (into `main`)
