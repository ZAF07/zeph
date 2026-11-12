# 05 — Flaky Knowledge document view test

Status: completed

## Symptom

`web/src/components/KnowledgeDocumentView.test.tsx` failed once during `make check-web`, then passed on its own:

```
TestingLibraryElementError: Unable to find an accessible element with the role "textbox" and name "Text of Mindful breathing"
```

Expected: the test passes every run. Impact: no product effect seen; it makes `make check` fail now and then, so a real failure can be mistaken for flakiness (or the other way round).

It happened on 2026-11-12 on branch `feat/13-usage-limits`, whose diff touches no Knowledge files. Which test case failed was not captured: the output only showed the error above. Several cases look up that textbox (lines 93, 202, 253, 286, 307, 326, 419, 488).

## Repro

Not deterministic. Seen once in a full run:

```
cd web && pnpm test
```

It then passed 3 of 3 full reruns (`pnpm vitest run`, 230 tests). To catch it, run the file many times, e.g. `pnpm vitest run src/components/KnowledgeDocumentView.test.tsx --repeat 50` or the full suite in a loop, and note which case fails.

## Acceptance criteria

- [x] The failing case is identified and the cause found (`/diagnosing-bugs`)
- [x] The test passes on many repeated runs (e.g. 50 in a row of the full suite)
- [x] `make check-web` passes (`pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`)

## Comments

**2026-11-12, diagnosed and fixed** (branch `fix/05-flaky-knowledge-document-view-test`).

- **Failing case:** "shows the document's details and its text in the editor". It waits for the page heading, then looks up the editor right away.
- **Cause (confirmed):** `CodeMirrorEditor` built the CodeMirror view in a `useEffect`. React puts the page in the DOM first and runs effects in a later task. RTL's `findBy` returns after one `setTimeout(0)`. On a busy machine (≥1ms gap) that timer runs before React's effects, so the heading is there but the editor isn't yet.
- **Repro:** 8 parallel runs of the file failed 5/40. A throwaway test that adds a 1–5ms busy-wait right after the commit failed 30/30.
- **Fix:** build the view in `useLayoutEffect`, so the editor is in the page as soon as the component is. Only the Knowledge text editor uses CodeMirror (the Persona and Crisis Reply editors are plain textareas).
- **Regression test:** `web/src/components/CodeMirrorEditor.test.tsx`. Red before the fix, green after.
- **Evidence:** the parallel loop failed 0/80 after the fix, the full suite passed 50/50 in a row, and `make check-web` passes (231 tests).
- **`/run` (rebuilt Docker stack, Clerk test user signed in by ticket, made Admin in the database, both deleted afterwards):** on "Noticing thoughts without following them" the editor was there on load, labelled and editable. Typing showed "Unsaved changes". Undo removed the typing, Bold worked, Find & replace opened its panel, and Discard restored the text to "Saved". At 390px the line numbers line up with wrapped lines. No page errors (only Clerk script loads cut off by navigation). Nothing was saved, and the document is unchanged in the database (`text_edited` false, Ready).

## Completion

- Completed: 2026-11-12
- Commit: fc2828f "Knowledge editing issue 05: fix flaky Knowledge document view test by building the CodeMirror editor in a layout effect"
