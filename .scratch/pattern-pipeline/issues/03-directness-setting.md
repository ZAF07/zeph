# 03 — Users set how direct Zeph is with its Read

Status: ready-for-agent
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 59, 60, 61, 62, 63). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Each User sets how direct the Companion is with its Read: gentle, balanced (to start) or direct. It changes how soon and how plainly the Read is said, never whether Zeph has one, and never whether a Pattern is ready. It is ignored while the User is struggling. Users change it on the Dashboard or by telling Zeph in chat (a Chat Setting Change, marked "Changed in chat"). The Reply Plan is given it as one more input.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] A User can pick gentle, balanced or direct on the Dashboard; balanced is the default for existing and new Users
- [ ] A User can change it in plain words in chat, and the Dashboard marks it "Changed in chat"
- [ ] The Reply Plan is given the setting, and the Reply Plan prompt says what each level means
- [ ] On gentle, a User who asks for Zeph's view still gets its Read
- [ ] While the Understanding says the User is struggling, the setting isn't given to the Reply Plan
- [ ] A Settings Eval case covers the chat change
- [ ] New Copy slots hold the setting's name, help text and level names
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments
