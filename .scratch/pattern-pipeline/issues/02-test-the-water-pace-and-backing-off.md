# 02 — Test the water, pace between Curiosities, and backing off after brush-offs

Status: ready-for-agent
Track: A
Blocked by: 01

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 9, 10, 12, 13, 14, 15, 77). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Being proactive must not turn banter into an interview. This slice adds the fourth choice for a Need's Curiosities field and the rules for how often Zeph asks, all as code with Admin-set numbers.

Test the water: Zeph may drop one light opener; if the User doesn't engage, none for the rest of the Conversation. Just chatting starts on it. Pace: a fewest replies between two Curiosities (start 3). Follow-ups on a story the User is telling right now (the Get curious Move) don't use the Curiosity budget and have their own cap per Conversation (start 3). Backing off: after brush-offs in a row (start 2), none for the rest of the Conversation and the spacing doubles for a time (start 3 days); one engaged answer ends it. A topic the User asked to drop stays dropped.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] A Need can be set to test the water; Just chatting starts on it
- [ ] Under test the water at most one Curiosity is offered as a light opener; after the User doesn't engage, none are offered for the rest of that Conversation
- [ ] No Curiosity is offered until the Admin-set number of replies has passed since the last one
- [ ] Get curious follow-ups on the User's current story don't count toward the Curiosity limit and stop at their own cap
- [ ] After the Admin-set number of brush-offs in a row, none are offered for the rest of the Conversation and the spacing is doubled for the Admin-set time
- [ ] One engaged answer returns the spacing to normal
- [ ] Each new number is a Platform Setting with a hint, and can be overridden in an Eval Variant
- [ ] The pace and backing-off rules are pure functions with their own tests
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`

## Comments

Plan (24 Nov 2026, branch `pattern-02-test-the-water`, worktree ports 3010/8010):

- **How Zeph knows a Curiosity was brushed off mid-Conversation.** Today the reaction is only judged when the Conversation ends. The Reply Plan of the next reply is now shown "the Curiosity Zeph asked in its last reply" and says how they took it (`curiosity_taken`: engaged / brushed off / asked to drop); code saves it on that Curiosity straight away. The Conversation-end keeping step still judges it again. With the fewest replies between Curiosities at least 1, the reply right after one can't ask another, so reading it there is in time. The Understanding stays free of Curiosities. `reply_plan_prompt` is reloaded from the seed by migration (as 0080 did, a day ago).
- **Pure rules in `core/curiosities.py`**, tested with plain values: brush-offs in a row (newest first, stopping at an engaged answer, unknown skipped); the replies needed (doubled while backing off); whether a Curiosity may be offered now; whether test the water still allows one. They run in `CuriosityRaiser.due`, before the Reply Plan call; test the water depends on the picked Need, so it runs in `offered_under`, like never.
- **Pace counts replies across Conversations** (Reply Plans since the newest Curiosity was raised): the live limit is 1 Curiosity per Conversation, so spacing inside one Conversation would do nothing.
- **Follow-ups (Get curious)**: code knows them as Moves that ask a question (`asks_a_question`), not by name. Once this Conversation's Reply Plans made the cap of them, none is offered. They never use the Curiosity budget.
- **Asked to drop stays dropped**: the keeping step is always shown every Curiosity the User asked to drop, not only the last 10 raised.
- **Settings** (seeded, editable with hints, so Variants can override them): `curiosity_replies_between` 3, `follow_ups_per_conversation` 3, `curiosity_brush_offs_to_back_off` 2, `curiosity_back_off_days` 3.
- **Needs**: new choice `test_the_water`; migration 0081 moves Just chatting to it (by name) and the seed starts it there.
- **Dashboard**: "Test the water" in the Needs select; four field rows in the Settings page's Curiosities group. No new parts, no reference edits.
