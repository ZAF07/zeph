# 25 — Reply doesn't ask about a Life Thread it was told to lead with

Status: needs-triage

## What

Found while tuning the Understanding (issue 17, 2026-11-15). In the Understanding eval case `reminded-of-sister` ("my sister's wedding is next week", with the open 9-month-old Falling-out with Mei Thread), the Understanding now picks `bring_up: [{"thread": 1, "how": "lead"}]` every time, but the reply sometimes only says something like "Mei's wedding. That's a big one. How are you feeling about it?" and doesn't ask how things are with Mei. The Judge's `raises_sister_naturally` rule then fails.

Pass rate of the reply rule after issue 17's wording: 8 of 10 runs (the Understanding's own checks passed every run). This is the reply prompt or how a led Thread is shown to the reply, not the Understanding.

Also seen in the same runs, also reply-side and older than issue 17: Persona `asks-for-tips` fails `no_lists` about half the time (2 of 4 runs here; 2 of 3 in issue 18's runs). The Advice reply writes tips as a list.

## Acceptance criteria

- [ ] `reminded-of-sister` passes in 3 Understanding eval runs in a row
- [ ] `asks-for-tips` passes in 3 runs in a row, or is split into its own issue

## Comments

- 2026-11-15, from issue 22's evals (reply on `deepseek-flash`, thinking off): two more reply-side flakes where the Understanding's checks passed. `strong-mood-unknown-cause` asked two questions at once (`gentle_probe`, 1 of 2 runs), and `brushed-off-not-raised-too-soon` asked how dad was though the Understanding left that Thread alone (`leaves_dad_alone`, 1 of 3 runs).
