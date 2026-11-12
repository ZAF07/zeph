# 15 — Eval suite and README

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

A way to measure the Companion's behaviour with the real LLM, run separately from normal checks with `make eval`. Safeguard evals use ~30 labelled messages (clear crises, subtle crises, false alarms like "this traffic is killing me"); the target is that every real crisis is caught. Persona evals run a few scripted conversations, judged by an LLM against the Persona rules (no bullet lists, no "As an AI…", not preachy, honest when asked if it's human, gentle about dependency).

Knowledge evals check that what an Admin puts in the Knowledge library actually reaches Users, and that an Admin's edits reach them too. Each case uploads a Knowledge Document holding a made-up teaching the model can't know from training. It then asks a User question it should draw on, and an LLM judge decides which version of the document the reply uses. The same document is then changed in each of the ways an Admin can change it. After each change, the eval waits for Ready and asks again:

1. **Text edited** (knowledge-editing issue 03): the reply uses the new text, not the old.
2. **Details edited** (title, source, tradition; issue 02): when asked where the idea comes from, the reply names the new title or source, not the old.
3. **File replaced** (issue 04): the reply uses the new file's text, not the old file's or the earlier edit's.

Any reply that still uses an old version is a failure. These evals go through the real reply path (the Telegram webhook endpoint, with a recording fake chat channel), using the real LLM and the real embedder, so no real Telegram chat is needed. A README explains how to run the evals, what they cost, and how to read the results.

## Acceptance criteria

- [ ] `make eval` runs Safeguard and Persona evals against the real configured LLM, using the current prompts from settings
- [ ] `make eval` is not part of `make check`
- [ ] Safeguard evals report each missed crisis and each false alarm, and fail if any real crisis is missed
- [ ] Persona evals report a pass/fail per rule per scripted conversation, with the judge's reason
- [ ] Knowledge evals upload a document with a made-up teaching, then check through the real reply path (webhook, real LLM and embedder) that the reply draws on it
- [ ] Knowledge evals then edit the text, edit the details, and replace the file. After each change they wait for Ready and check that the next reply uses the new version and not the old one, with the judge's reason
- [ ] Knowledge evals fail if any reply uses an old version of a document
- [ ] The eval cases are data files, easy to add to
- [ ] An eval README explains: setup, how to run, rough cost, how to read results, when to run (after changing Safeguard or Persona prompts or models, the Knowledge intro or chunks-per-reply settings, the embedding model, or how Knowledge is read, indexed or retrieved)
- [ ] `make check` passes
- [ ] `make eval` has been run once and its output reported

## Blocked by

- `.scratch/mvp/issues/archive/05-safeguard.md` (done)
- `.scratch/mvp/issues/archive/08-knowledge.md` (done)
- `.scratch/knowledge-editing/issues/archive/02-edit-knowledge-details.md`, `03-edit-knowledge-text.md`, `04-replace-knowledge-file.md` (done)
