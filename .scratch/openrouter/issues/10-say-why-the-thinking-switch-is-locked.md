# 10 — Say why the thinking switch is locked

Status: ready-for-agent
Blocked by: 07

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Asked for by the operator on 2026-11-25, after issue 07.

## What to build

In Prompts and models, the thinking switch is locked for a model that can't think (issue 07), but nothing says why. When an Admin holds the mouse over the locked switch, a small pop-up says why. The page at rest looks the same as today, so the design reference does not change (operator's decision, 2026-11-25). The pop-up is made only from values the design already has.

## Acceptance criteria

- [ ] Holding the mouse over a locked thinking switch shows a pop-up saying the model can't think
- [ ] A switch that is not locked shows no pop-up
- [ ] A screen reader is told the same reason (test)
- [ ] `/run`: the pop-up is seen in the browser at 1280 and 390, and `AdminPrompts` still passes the pixel test
- [ ] The language's checks pass

## Blocked by

- 07

## Comments

- 2026-11-25, in progress on branch `openrouter-10-why-thinking-is-locked` (worktree `ai-chat-companion-openrouter-10`).
