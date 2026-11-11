# 08 — Knowledge

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion draws on a curated Knowledge library, starting with mindfulness. Introduces the embedder port (fastembed, small local BGE model) and vector store port (pgvector).

Admins upload documents (text, Markdown, PDF) with title, source/author and tradition. Each document is split into chunks, embedded and stored; its status moves pending → ready / failed. When composing a reply, the top few matching chunks are added to the prompt, and the prompt tells the Companion to use them only when they genuinely fit, without lecturing. A starter mindfulness set (public-domain texts plus the owner's summaries) is seeded from data files.

## Design

- `docs/design/zeph-admin.html`: Knowledge

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] Admins can upload text, Markdown and PDF Knowledge documents with title, source/author and tradition
- [ ] Uploaded documents are chunked, embedded and stored; status shows pending, ready or failed
- [ ] Admins can list and delete documents; deleting removes their chunks
- [ ] Relevant chunks are included when composing a reply
- [ ] A starter mindfulness Knowledge set is seeded from data files
- [ ] The embedder and vector store are behind ports and chosen via `.env`
- [ ] Seam 1 tests with a fake embedder cover upload → ready, failed extraction → failed, and matching chunks reaching the prompt
- [ ] A separate contract test checks the fastembed adapter returns embeddings of the expected size
- [ ] Seam 3 tests cover the admin Knowledge page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`

## Comments

**2026-11-11 — started on branch `feat/08-knowledge`.** Plan: ports for embedder (fastembed BGE small, 384 dims), vector store (pgvector) and document text extraction (pypdf); `KnowledgeService` (upload → pending → background ingestion → ready/failed, retry, delete, starter seed); `KnowledgeRetrieval` step before response composition; admin API under `/api/admin/knowledge-documents`; `/admin/knowledge` page.
