# 19 — The Understanding picks Knowledge documents by number, not by copying titles

Status: ready-for-agent

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

- [ ] The Understanding reads numbered Knowledge documents and answers with numbers; the chosen documents' passages reach the reply
- [ ] A number not in the list, or a title instead of a number, picks nothing and doesn't crash
- [ ] Tests at the webhook seam cover both
- [ ] The seeded Understanding prompt is updated, with a migration for existing installs
- [ ] The saved Understanding records which documents were chosen by title or ID, not by list number
- [ ] The Knowledge eval (with `RunningClock`) and the Understanding eval's Knowledge cases pass at least as often as after bug 16
- [ ] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` pass

## Blocked by

- `.scratch/understanding/issues/archive/16-knowledge-dropped-when-document-named-by-its-whole-line.md` (done)

## Comments

- 2026-11-15: Raised after bug 16. Picking from a fixed set means there's nothing to copy wrong. Another option is to make the answer's format allow only the listed titles (a JSON schema enum); numbers were chosen because they also work with models and providers that don't enforce schemas.
