# 07 — Knowledge "when it helps", chosen by the Understanding

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Knowledge comes in only when it genuinely fits. Each Knowledge Document gets a "when it helps" description: drafted by a model when the document is made ready (Starter Knowledge included), editable by Admins on the document's page, used by replies straight away. The Understanding sees every Ready document's description and, in its `knowledge` field, picks documents and a search phrase, or nothing. Embeddings then find the closest passages only inside the chosen documents, above an Admin-set closeness bar, at most `knowledge_chunks_per_reply`. Nothing is searched when `knowledge` is empty or the Knowledge Feature doesn't work for the User. The old "newest text only" search is removed.

## Acceptance criteria

- [x] Indexing a document drafts "when it helps"; a failed draft doesn't fail the document (it can be filled in by an Admin)
- [x] Admins edit it on the document page; Vitest + RTL test
- [x] The Understanding is given the descriptions; with no documents chosen, the reply gets no Knowledge
- [x] With documents chosen, passages come only from them, and a weak match adds nothing
- [x] Knowledge Feature off → nothing searched, as today
- [x] Existing Knowledge Evals still pass
- [x] Checks pass (backend and `pnpm`)
- [x] `/run`: a vent gets no Knowledge; a reflective question gets a passage from a fitting document

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`

## Comments

- Branch `understanding-07-knowledge-when-it-helps`, worktree `ai-chat-companion-understanding-07`.
- Decisions:
  - `knowledge_documents.when_it_helps` (text, default ""), migration 0031 (renumbered after issue 08's 0030 on rebase); it also reloads the Understanding prompt, which now explains `knowledge`.
  - Drafting: when a document is indexed and its "when it helps" is blank, one model call (Admin-set prompt and model, on Prompts and Models) drafts it from the title, source, tradition and the start of the text, before the document is marked Ready. A failed draft is logged and the document is still Ready. Text edits and file replacements keep the description (CONTEXT.md: replacing a file keeps its details).
  - Admins edit it with the other details (PATCH `/api/admin/knowledge-documents/{id}`), in the Details card. Blank is allowed.
  - The Understanding sees every Ready document (title, source, tradition, when it helps) while Knowledge works for the User, and answers `knowledge` as `{"documents": ["<title>"], "search": "<phrase>"}` or `null`.
  - Search: only when documents and a phrase were given; embeddings search only inside the chosen Ready documents, at or above `knowledge_closeness_percent`, at most `knowledge_chunks_per_reply`. The old latest-text search goes. Documents are matched by title, ignoring case.
  - A draft only fills a blank "when it helps", checked in the same database update, so an Admin's edit saved while a draft is written is kept.
  - Drafting uses the plain chat model, not the usage-recording one: it is for no User, so it isn't in usage or the Model Call Log (which is per Message or Check-in). A failed draft is logged.
  - The settings are `knowledge_when_it_helps_prompt` / `knowledge_when_it_helps_model` (Prompts and Models, as the Core Service "Knowledge “when it helps”") and `knowledge_closeness_percent` (Settings → Knowledge, seed 60).
  - Tuned from real runs (bge-small embedder):
    - The closeness bar is 60, not 65. Inside the chosen documents, fitting passages scored 0.64–0.74 and unrelated text about 0.50. One fitting passage scored 0.646, which a 65 bar dropped.
    - The Understanding prompt asks for the search phrase in a passage's words (the topic or practice), not the User's question. "how to stop beating myself up…" scored 0.59 against the fitting passage; "being kind to yourself after a mistake…" scored 0.64–0.74.
    - The drafting prompt names the practices or teachings a document covers, and the Understanding also picks a document asked about by name. Without this, the Knowledge Eval's "details edited" step failed once (7/8): after a rename, "Where does the Pebble Practice come from?" found nothing.
  - Documents made ready before this change have no description until they are indexed again or an Admin writes one. No backfill, as the platform isn't live; the main stack's starter documents are in this state.
  - Also fixed: the Eval client wasn't passing the `timer` that `CompanionTestClient` now needs, so `make eval` errored on main.

## Evidence

- **Indexing drafts "when it helps"; a failed draft doesn't fail the document:**
  - `tests/test_knowledge_when_it_helps.py::test_indexing_a_document_drafts_when_it_helps` (the draft model gets the title, source and text, and the answer is trimmed).
  - `test_a_failed_draft_still_makes_the_document_ready_with_no_description`.
  - `test_reindexing_keeps_a_description_and_drafts_a_missing_one` (a later re-index fills a blank).
  - Starter Knowledge: `tests/test_knowledge_seed.py::test_the_starter_mindfulness_set_is_seeded_ready_from_the_data_files` (every starter document has a description).
  - Race: `tests/test_knowledge_reindex.py::test_a_draft_never_overwrites_an_admins_edit_saved_meanwhile`.
  - Real app: on a fresh worktree database, all 6 starter documents got real DeepSeek drafts, e.g. Self-compassion: "When someone is being hard on themselves after a mistake or failure and needs a way to respond with warmth instead of criticism, this offers Kristin Neff's three-part self-compassion framework…".
- **Admins edit it on the document page; Vitest + RTL:**
  - `web/src/components/KnowledgeDocumentView.test.tsx`: "edits when the document helps, and replies use it straight away" and "asks for when it helps when the draft is missing".
  - API: `test_an_admin_edits_when_it_helps_and_the_next_understanding_sees_it` (PATCH trims it, and the next Understanding is given the new text).
  - Real Dashboard (run-dashboard, Admin): `/admin/knowledge/<Self-compassion>` showed the drafted text; it was edited, saved and reloaded with the new text kept. Checked at 390px. `/admin/settings` showed "Knowledge closeness bar"; `/admin/prompts` listed the "Knowledge “when it helps”" service. No page errors.
- **The Understanding is given the descriptions; with no documents chosen, the reply gets no Knowledge:**
  - `test_an_admin_edits_when_it_helps_and_the_next_understanding_sees_it` and `test_the_understanding_sees_only_ready_documents`.
  - `test_with_no_documents_chosen_the_reply_gets_no_knowledge`: no Knowledge intro or passage, and the only search is the Life Threads search of the User's own text.
  - `test_an_unknown_document_title_or_a_missing_phrase_searches_nothing`.
- **With documents chosen, passages come only from them, and a weak match adds nothing:**
  - `test_passages_come_only_from_the_chosen_documents`.
    - Mutation check: with the adapter's `document_id IN (chosen)` filter removed, this test fails. Better matches from unchosen documents fill the 3-passage limit and push out the chosen document's passage.
  - `test_a_weak_match_in_a_chosen_document_adds_nothing` and `test_the_admin_sets_the_knowledge_closeness_bar` (99 drops the passage, 0 lets it in). Dashboard: `PlatformSettingsForm.test.tsx` "shows and saves the Knowledge closeness bar".
- **Knowledge Feature off → nothing searched:**
  - `tests/test_features.py::test_with_knowledge_off_no_passages_go_into_the_reply` (no Knowledge searches while off) and `test_with_knowledge_off_for_one_user_others_still_get_passages`.
  - While off, the Understanding is shown no documents.
- **Existing Knowledge Evals still pass:**
  - `uv run pytest evals -m eval -k knowledge` on the rebased code: 8 of 8 steps right (52,770 tokens in, 3,419 out). Every step passed: uploaded, text edited, details edited and file replaced, for both lantern-breath and pebble-practice.
- **Checks pass:**
  - Python: `ruff check`, `ruff format --check` and `mypy` are clean. `pytest` 845 passed, 9 deselected (on the branch rebased onto main after issues 08 and 09).
  - Web: `pnpm lint`, `pnpm format:check` and `pnpm typecheck` are clean; `pnpm test` 358 passed.
- **/run** (real worktree app in a one-off backend container: real Postgres, DeepSeek and fastembed, only the Telegram channel recorded; an Admin User so the Model Call Log keeps full content):
  - A vent ("my manager just took credit for my whole project… I'm so angry I could scream"): Need Be heard, `knowledge: null`, no Knowledge in the reply.
  - A reflective question ("I keep beating myself up over a mistake… how do people stop being so hard on themselves?"): Need Think it through. `knowledge` was {documents: [Self-compassion, Noticing thoughts without following them], search: "responding to self-criticism with self-kindness and stepping back from repetitive harsh thoughts"}. The reply got "From “Self-compassion” (Owner’s summary, after Kristin Neff, Psychology): …" (closeness 0.743). Meditations scored 0.660 but wasn't chosen, so it stayed out.
  - Small talk ("just had the best ramen of my life"): Just chatting, no Knowledge.
  - The Understanding's input held every document's "when it helps".
- **/code-review:**
  - Standards: no hard violations.
    - Fixed: renamed the settings to `knowledge_when_it_helps_*`; the TSDoc now explains the form remount; the migration was renumbered.
    - Kept as they are: the Ready filter in both the Understanding and retrieval (each module stays self-contained); reading stored forms with `read_knowledge_lookup` (it turns old list-shaped rows into None); the fake's extra prompt branch (an existing pattern).
  - Spec: nothing missing.
    - Fixed: a draft could overwrite an Admin's edit saved meanwhile.
    - Kept: two documents with the same title are both searched (rare, harmless).

## Completion

- Completed: 2026-11-14
- Commits: `397fae5` (Knowledge "when it helps", chosen by the Understanding; includes the review fixes and the Eval client fix, squashed before rebasing onto issue 08), `77f1d62` (issue archived with evidence), `b16ccff` (CONTEXT.md: how the Understanding chooses Knowledge)
- Merged into main: `849ebfe` (branch `understanding-07-knowledge-when-it-helps`, pushed to origin)
