# 09 — Life Threads on the Memories page

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

Users see "What's going on in your life" on the Memories page: each Life Thread's story, open or settled, and when it was last updated. They can delete one, on the Dashboard or by saying "forget the thing about my sister" in chat (the existing "forget a Memory Item" Chat Setting Change extended to Threads, with Settings in Chat rules as today). Deleting removes it from replies at once. No editing.

## Acceptance criteria

- [ ] Dashboard API: list and delete the User's own Threads
- [ ] Memories page section following `docs/design/zeph-product.html` where it fits; Vitest + RTL tests
- [ ] "Forget that" in chat deletes a Thread and the Dashboard marks it "Changed in chat" where that applies
- [ ] A deleted Thread is never reminded or raised again
- [ ] Shown whether User Memory is on or off
- [ ] Checks pass (backend and `pnpm`)
- [ ] `/run-dashboard`: see and delete a Thread; `/run`: forget one in chat

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md`
