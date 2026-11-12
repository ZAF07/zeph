# 05 — Flaky Knowledge document view test

Status: needs-triage

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

- [ ] The failing case is identified and the cause found (`/diagnosing-bugs`)
- [ ] The test passes on many repeated runs (e.g. 50 in a row of the full suite)
- [ ] `make check-web` passes (`pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`)
