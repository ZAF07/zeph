# 21 — AdminUsers fails the pixel test

Status: needs-triage

## Parent

`.scratch/redesign/PRD.md` (found while closing `.scratch/pattern-pipeline/issues/archive/10-pattern-catalog-loads-and-admins-read-it.md`)

## Symptom

The pixel test fails for the Admin Users page:

```
FAIL  AdminUsers                         2.80% differs, height 800 vs 933
```

Expected: PASS, as the page is already built.

This is not the known annotation-section gap in issue 19: `web/design/reference/AdminUsers.html` has no annotation section, and 2.80% is far more than those pages differ by. The cause is not known.

Seen on 24 Nov 2026, with the same numbers on `main` before and after the Pattern Catalog work, so the new menu link did not cause it.

## Repro

Deterministic on this machine. Needs the workaround from issue 20, or the run hangs.

1. Follow steps 1 to 5 of `.scratch/redesign/issues/20-pixel-test-hangs-on-clerk-probes.md`
2. Run the copy of `compare.cjs` that blocks `protect.clerk.com`, with `AdminUsers`

## Acceptance criteria

- [ ] The cause is recorded here
- [ ] `node web/design/compare.cjs AdminUsers` prints PASS
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`

## Comments
