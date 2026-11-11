# 08 — Knowledge

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion draws on a curated Knowledge library, starting with mindfulness. Introduces the embedder port (fastembed, small local BGE model) and vector store port (pgvector).

Admins upload documents (text, Markdown, PDF) with title, source/author and tradition. Each document is split into chunks, embedded and stored; its status moves pending → ready / failed. When composing a reply, the top few matching chunks are added to the prompt, and the prompt tells the Companion to use them only when they genuinely fit, without lecturing. A starter mindfulness set (public-domain texts plus the owner's summaries) is seeded from data files.

## Design

- `docs/design/zeph-admin.html`: Knowledge

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Admins can upload text, Markdown and PDF Knowledge documents with title, source/author and tradition
- [x] Uploaded documents are chunked, embedded and stored; status shows pending, ready or failed
- [x] Admins can list and delete documents; deleting removes their chunks
- [x] Relevant chunks are included when composing a reply
- [x] A starter mindfulness Knowledge set is seeded from data files
- [x] The embedder and vector store are behind ports and chosen via `.env`
- [x] Seam 1 tests with a fake embedder cover upload → ready, failed extraction → failed, and matching chunks reaching the prompt
- [x] A separate contract test checks the fastembed adapter returns embeddings of the expected size
- [x] Seam 3 tests cover the admin Knowledge page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`

## Comments

**2026-11-11 — started on branch `feat/08-knowledge`.** Plan: ports for embedder (fastembed BGE small, 384 dims), vector store (pgvector) and document text extraction (pypdf); `KnowledgeService` (upload → pending → background ingestion → ready/failed, retry, delete, starter seed); `KnowledgeRetrieval` step before response composition; admin API under `/api/admin/knowledge-documents`; `/admin/knowledge` page.

**2026-11-12 — implemented, reviewed and verified.** Commits `c736b35`, `f0f9546` on `feat/08-knowledge`.

Done and verified: every acceptance criterion except the signed-in browser check of `/admin/knowledge`. `make check` green (Python 162, web 134). Docker run with real fastembed, pgvector and DeepSeek: prestart seeded the 6 starter documents (84 chunks); txt/md/pdf uploads became ready; scanned and broken PDFs failed with their reasons; a simulated indexing failure was retried to ready; `.docx` refused (422); non-Admin 403; delete removed the chunks; a racing-thoughts message got the mindful-breathing and noticing-thoughts passages and DeepSeek used them lightly. A document left pending by a restart is finished on the next start.

Decisions: ingestion runs after the upload response (FastAPI background task); prestart finishes any document still pending. The uploaded file is stored so Retry works (failed documents only). Text extractor is a port too (`TEXT_EXTRACTOR_ADAPTER=pypdf`). New seeded settings `knowledge_chunks_per_reply` (3) and `reply_knowledge_intro`. Chunks ≤1,000 characters by paragraph. Starter set: Dhammapada (Müller), Meditations II & IV (Casaubon), Tao Te Ching selections (Legge), all public domain from Project Gutenberg, plus three summaries drafted for the owner to review (`mindful-breathing.md`, `noticing-thoughts.md`, `self-compassion.md`).

Browser check (owner approved a temporary Clerk test user, deleted afterwards along with its database row): Chrome for Testing signed in as an onboarded Admin. The sidebar shows Knowledge as the current page. The 6 starter documents are listed ready. Uploading a .txt suggested the title "walking practice" and showed it as Text, Ready. A broken PDF showed Failed, "Couldn’t read this PDF.", with Retry; retrying left it failed with the same reason. Deleting both asked for confirmation and removed them. At 390px there is no sideways scroll.

Caveats / follow-ups:
- The three "Owner’s summary" seed texts were drafted for the owner; review or replace them. Deleting one in the admin area is permanent: seeding only runs on an empty library.
- The traditions dropdown is a fixed list in the Dashboard; the backend accepts any tradition.
- Embedding size 384 is fixed in migration 0007 and must match the fastembed model; the contract test (`make contract`) checks it.
- Seen during the browser run, not from this issue: right after sign-in the Dashboard's first `/api/me` calls got 401 until a reload.

Evidence: seam 1 `tests/test_knowledge.py` (13), `tests/test_knowledge_seed.py` (3), `tests/test_knowledge_chunks.py` (4), `tests/test_config.py`; contract `test_fastembed_embeddings_have_the_size_the_vector_store_keeps` (passed, real model); seam 3 `web/src/components/KnowledgeLibrary.test.tsx` (10), `SidebarNav.test.tsx`, `dates.test.ts`. `make check`: Python 162 passed, web 134 passed, ruff, ruff format, mypy, eslint, prettier, tsc clean.

## Completion

- Completed: 2026-11-12
- Commit: c736b35, review fixes f0f9546 (merged from `feat/08-knowledge` in dd52c10)
