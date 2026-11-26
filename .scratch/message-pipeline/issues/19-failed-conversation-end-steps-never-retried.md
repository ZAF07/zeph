# 19 — A failed Conversation-end step is never tried again (except the Day Summary)

Status: needs-triage

## Symptom

When a Conversation ends, `PostConversationProcessor.process` runs its steps in order. Only the Day Summary step is tried again when it fails: its model error is raised, the Conversation stays unprocessed and the next tick runs it again.

Every other step is wrapped in its own try/except that logs and moves on:

- Life Threads (`_keep_life_threads`)
- Pattern tagging (`_tag_observations`)
- settling reactions and shared Patterns, scoring, the ready gate
- Pattern keeping
- Curiosities, the Agenda, starter Thought Experiments, Prediction follow-ups
- Move Outcomes
- the Portrait

Once the Day Summary step has marked the Conversation processed, a later step that fails (for example a model timeout during tagging) is never run again for that Conversation. Expected: what Zeph should have learned from it is kept once the failure passes. Actual: it is lost for good, with only a log line. For example, no Observations are tagged and no Life Thread is updated.

Impact: no crash, but User Memory and Pattern evidence go missing without anyone being told. It gets worse under load or when the model provider is having trouble.

## Repro

Not reproduced yet. Expected path:

1. End a Conversation with User Memory and Pattern noticing on.
2. Make the tagging model call raise (e.g. a fake chat model that raises for `ModelStep.PATTERN_TAGGING`).
3. See "Could not tag Observations" logged, and the Conversation marked processed.
4. Run the next tick: tagging isn't tried again, and no Observations exist for that Conversation.

Deterministic once a step's call raises.

## Suspected location

`src/companion/core/post_conversation.py`: `process` (about lines 764–829) and the per-step `_keep_*` / `_tag_observations` / `_score_patterns` / `_check_ready` wrappers that catch `Exception` and log. The Day Summary is marked processed in `DayMemoryWriter.write` (`save_processed_conversation`).

## Acceptance criteria

- [ ] A Conversation-end step that fails is tried again later (or the decision not to retry a given step is recorded, with why), without running steps that already succeeded twice
- [ ] Retries are safe to repeat (no duplicate Observations, Life Thread changes or Curiosities)
- [ ] A test covers a failed step being tried again
- [ ] Checks pass: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest`

## Comments
