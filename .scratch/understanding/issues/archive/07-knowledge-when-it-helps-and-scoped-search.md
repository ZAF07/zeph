# 07 — Knowledge "when it helps", chosen by the Understanding

Status: in-progress

## Parent

`.scratch/understanding/PRD.md`

## What to build

Knowledge comes in only when it genuinely fits. Each Knowledge Document gets a "when it helps" description: drafted by a model when the document is made ready (Starter Knowledge included), editable by Admins on the document's page, used by replies straight away. The Understanding sees every Ready document's description and, in its `knowledge` field, picks documents and a search phrase, or nothing. Embeddings then find the closest passages only inside the chosen documents, above an Admin-set closeness bar, at most `knowledge_chunks_per_reply`. Nothing is searched when `knowledge` is empty or the Knowledge Feature doesn't work for the User. The old "newest text only" search is removed.

## Acceptance criteria

- [ ] Indexing a document drafts "when it helps"; a failed draft doesn't fail the document (it can be filled in by an Admin)
- [ ] Admins edit it on the document page; Vitest + RTL test
- [ ] The Understanding is given the descriptions; with no documents chosen, the reply gets no Knowledge
- [ ] With documents chosen, passages come only from them, and a weak match adds nothing
- [ ] Knowledge Feature off → nothing searched, as today
- [ ] Existing Knowledge Evals still pass
- [ ] Checks pass (backend and `pnpm`)
- [ ] `/run`: a vent gets no Knowledge; a reflective question gets a passage from a fitting document

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`

## Comments

- Branch `understanding-07-knowledge-when-it-helps`, worktree `ai-chat-companion-understanding-07`.
- Plan:
  - `knowledge_documents.when_it_helps` (text, default ""), migration 0030; it also reloads the Understanding prompt, which now explains `knowledge`.
  - Drafting: when a document is indexed and its "when it helps" is blank, one model call (Admin-set prompt and model, on Prompts and Models) drafts it from the title, source, tradition and the start of the text, before the document is marked Ready. A failed draft is logged and the document is still Ready. Text edits and file replacements keep the description (CONTEXT.md: replacing a file keeps its details).
  - Admins edit it with the other details (PATCH `/api/admin/knowledge-documents/{id}`), in the Details card. Blank is allowed.
  - The Understanding sees every Ready document (title, source, tradition, when it helps) while Knowledge works for the User, and answers `knowledge` as `{"documents": ["<title>"], "search": "<phrase>"}` or `null`.
  - Search: only when documents and a phrase were given; embeddings search only inside the chosen Ready documents, at or above `knowledge_closeness_percent`, at most `knowledge_chunks_per_reply`. The old latest-text search goes.
