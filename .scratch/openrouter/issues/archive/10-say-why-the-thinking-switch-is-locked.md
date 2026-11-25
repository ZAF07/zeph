# 10 — Say why the thinking switch is locked

Status: completed
Blocked by: 07

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Asked for by the operator on 2026-11-25, after issue 07.

## What to build

In Prompts and models, the thinking switch is locked for a model that can't think (issue 07), but nothing says why. When an Admin holds the mouse over the locked switch, a small pop-up says why. The page at rest looks the same as today, so the design reference does not change (operator's decision, 2026-11-25). The pop-up is made only from values the design already has.

## Acceptance criteria

- [x] Holding the mouse over a locked thinking switch shows a pop-up saying the model can't think
- [x] A switch that is not locked shows no pop-up
- [x] A screen reader is told the same reason (test)
- [x] `/run`: the pop-up is seen in the browser at 1280 and 390, and `AdminPrompts` still passes the pixel test
- [x] The language's checks pass

## Blocked by

- 07

## Comments

- 2026-11-25, in progress on branch `openrouter-10-why-thinking-is-locked` (worktree `ai-chat-companion-openrouter-10`).
- 2026-11-25, done. Evidence:
  - Built: `HoverNote` (new, `web/src/components/HoverNote.tsx`) wraps the thinking switch in `CoreServiceCard`. While the chosen model can't think, holding the mouse over the switch shows "This model can’t think, so thinking stays off." in a small box to the left of the switch. `Switch` takes a `describedById`, so the locked switch is described by the same words. The box uses the dialog background, the line border, the input radius and the 13px soft hint text.
  - Criteria 1 and 2 (`/run`, worktree stack, signed in as an Admin in a real browser, with `deepseek/deepseek-v4-pro-0813` put in `models_that_cannot_think` by SQL and Response composition set to it): the pop-up was hidden before the mouse came, shown with those words while the mouse was over the locked switch, and hidden again after. Safeguard's switch (a model that can think) had no pop-up.
  - Criterion 3: `PromptsAndModels.test.tsx` checks the locked switch has that accessible description and an unlocked one has none; `HoverNote.test.tsx` checks the note with and without words.
  - Criterion 4: seen at 1280 and 390 (screenshots looked at). It first opened above the switch and covered the model picker (1280) and the row's name (390), so it was moved to the left of the switch, where it covers nothing at either width. `AdminPrompts` pixel test PASS (0.11% differs, height 1392 vs 1392), from a copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes; the copy was deleted afterwards.
  - Criterion 5: `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 965 passed. No backend files changed.
  - Code review (standards and spec, one agent): fixed the note's prop name and docstring, and gave `HoverNote` its own test.
  - Caveats:
    - Mouse only, as asked. A phone has no hover, and a locked switch can't take keyboard focus, so on a phone or by keyboard the pop-up does not show. A screen reader still gets the words.
    - Three values are new to the Dashboard: the box's 200px widest width, its 8px gap from the switch and its stacking order (`z-10`).
    - The design fixtures have no locked switch, so the pixel test does not cover the pop-up itself.
    - The naming fixes after the review were not rebuilt into the running stack; they change no markup.

## Completion

- Completed: 2026-11-25
- Commit: 422ede3 (merge of openrouter-10-why-thinking-is-locked; work in 1a0f3bf 6961146)
