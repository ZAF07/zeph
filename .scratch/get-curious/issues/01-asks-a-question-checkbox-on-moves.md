# 01 — "Asks a question" checkbox on Moves

Status: in-progress

## Parent

`.scratch/get-curious/PRD.md`

## What to build

Admins can tick **Asks a question** on any Move. A Move with it ticked follows two rules in every reply:

- **Never twice in a row.** If the previous Understanding in the Conversation made it, as lead or supporting, it isn't offered to the Understanding this time. It's offered again the reply after.
- **One question per reply.** If the Understanding makes it while the reply also asks why (the existing ask-why rule) or raises a Curiosity, the other question wins. The Move is dropped from that reply: it isn't put in the reply's instructions and isn't recorded as made, so no Move Outcome is kept for it. If it was the lead Move, the supporting Move doesn't move up; the reply just responds.

When the reply already asks a question (through such a Move, asking why or a Curiosity), the Woven-in Check-in model is told so, and prefers to leave the Check-in out or weave it in without another question.

The checkbox is shown and saved on the Dashboard Moves page and through the admin Moves API, and is off by default. Eval Runs keep it in their Moves snapshot. A Variant's Setting Overrides can't change it, as with a Move's needed Feature. Code never looks up a Move by name: this works for any Move with the box ticked. Get curious itself is added in issue 03.

## Parallel work: avoid clashes

Issue 02 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 02 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Understanding code:** you own the Move-offering filter (next to the needed-Feature filter), the reply-guidance or Move instructions, and how a made Move is recorded. Don't touch how due Curiosities are written out for the Understanding or the reply; 02 owns that.
- **Platform settings seed:** you only touch the Woven-in Check-in wording. 02 edits the Curiosity-keeping prompt.
- **Models and tables:** you change Move only; 02 changes Curiosity.

## Acceptance criteria

- [ ] A Move has an "asks a question" setting, default off, saved by a migration (the existing Moves get false) and in the Moves seed format
- [ ] The admin Moves API saves and returns it; a test covers create and update
- [ ] The Dashboard Moves page shows a checkbox for it on each Move and saves it; a Vitest test covers it
- [ ] A Move with it ticked that the previous Understanding made, as lead or supporting, isn't offered to the Understanding; it's offered again the reply after (webhook test with the scripted chat model)
- [ ] A Move with it ticked that is made together with asking why is dropped from the reply instructions and isn't recorded as made; the same applies when a Curiosity is raised
- [ ] A dropped lead Move doesn't let the supporting Move take its place
- [ ] The Woven-in Check-in model is told when the reply already asks a question
- [ ] The Eval Run Moves snapshot keeps the setting; Setting Overrides can't change it
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`; in `web/`: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] `/run`: on the Dashboard, tick the box on a Move and see it saved. In the running app, a Message whose scripted or real Understanding made that Move doesn't get it offered on the next Message (seen in the Model Call Log or the understandings table)

## Blocked by

None - can start immediately.

## Comments

- 2026-11-18 (agent, branch `get-curious-01-asks-a-question`): started. Plan: `asks_a_question` on Move (model, table, migration 0058 which also reloads the Woven-in Check-in prompt, repo, seed loader, admin API, eval snapshot; Setting Overrides keep the live value). Understanding: filter out a ticked Move the previous Understanding made, next to the needed-Feature filter; after picking, drop ticked lead/support when the reply asks why or raises a Curiosity (support never moves up). Woven-in Check-in told when the reply already asks a question. Dashboard: checkbox on each Move card.

