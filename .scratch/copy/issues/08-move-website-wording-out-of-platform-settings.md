# 08 — Copy: move website wording out of Platform Settings

Status: ready-for-agent

Lane: whichever lane is free first.

## Parent

`.scratch/copy/PRD.md`

## What to build

The website wording that is a Platform Setting today becomes Copy, so every website word has one home:

- AI notice and short AI notice
- User Memory explanation and Photo Viewing explanation
- "Memory is paused" and "Memory isn't available" notes, each split into a title slot and a body slot (the title and body of the design's "Memory is off" notice in `States`, as `PausedNotice` draws them; no `**` markup remains)
- Delete My Data description

Each moves into the Copy tab of the page that shows it (Shared if more than one page shows it). The Settings page drops these fields. Endpoints that sent this wording inside other data (e.g. the Home data and the signed-in User's Memory note) stop sending it; the web app picks the right slot from the flags it already gets. A migration drops the old settings; no backfill (the platform isn't live).

Stays as is: the onboarding reason choices and all chat wording (Platform Settings), and the Crisis Reply (Safety).

## Acceptance criteria

- [ ] Each listed wording is a Copy slot on the right tab and no longer a Platform Setting (not in the settings read or save, not on the Settings page).
- [ ] The Memory notes show as `PausedNotice` title and body, exactly as the "Memory is off" notice in `States` draws them, picked by the User's Memory flags.
- [ ] No endpoint sends this wording outside the Copy reads.
- [ ] Onboarding reason choices, chat wording and the Crisis Reply are untouched.
- [ ] Seed text matches the references; the pixel test passes for every page showing this wording at both widths.
- [ ] Tests cover the move and the note picking; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit the "Memory is paused" lead, turn Memory off as a User and see it bold on Home and Memories; the Settings page no longer shows these fields.

## Blocked by

- `.scratch/copy/issues/03-onboarding.md`
- `.scratch/copy/issues/05-home-and-connect-telegram.md`
- `.scratch/copy/issues/06-memories.md`
- `.scratch/copy/issues/07-check-ins-and-account.md`

## Comments

- 2026-11-19 — From issue 05: Home and the Dashboard menu read Copy now, except the AI notice (Home's footer, from `/home`'s `ai_notice`), the short AI notice (`SidebarAiNotice`, from Platform Settings) and the Memory-off note (`HomeMemoryLine`'s `note`, with `**bold**`). Home's "Memory is on." note is already Copy (`home.memory.on_title`, `on_body`); the paused and not-available notes can sit next to it in the Home tab. The frame gives the menu only `shared.dashboard.*` and `shared.wordmark` (`DashboardFrame` `pickCopy`); widen it when the short AI notice moves.
