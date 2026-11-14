# 13 — Clear wording: User Memory off vs Delete My Data

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

Users must understand that User Memory off never deletes anything (it only stops learning) and that Delete My Data removes everything, private notes included. All wording is Admin-editable seed text.

- **Consent** (Onboarding): the User Memory explanation gains an honest line that the Companion also keeps private notes to follow up with them, which they won't see and which Delete My Data removes. It no longer claims everything is listed on the Dashboard.
- **Turning User Memory off in chat:** the confirmation always includes a fixed Admin-set line ("Nothing is deleted. I'll still use what I know, I just won't learn anything new. Use Delete My Data to remove everything.").
- **Delete My Data prompts** (chat and Dashboard) say they remove all memories and private notes.
- Dashboard notes for memory off already say it stops learning; check they mention Delete My Data.

## Acceptance criteria

- [ ] Seed wording updated; each line editable by Admins
- [ ] Turning User Memory off in chat always sends the fixed line (webhook-seam test with scripted settings tool call)
- [ ] Delete My Data prompts mention private notes, in chat and on the Dashboard (backend and Vitest tests)
- [ ] Settings Eval still passes
- [ ] Checks pass (backend and `pnpm`)
- [ ] `/run`: turn memory off in chat and see the fixed line; `/run-dashboard`: see the consent and Delete My Data wording

## Blocked by

- `.scratch/understanding/issues/11-curiosities.md`
