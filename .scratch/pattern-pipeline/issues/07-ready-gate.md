# 07 — Ready gate: code decides when a Pattern may be shared

Status: ready-for-agent
Track: A
Blocked by: 04

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 26, 27, 30, 31, 66). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A Pattern becomes ready only when code finds all ten checks true (listed in `docs/pattern-pipeline/README.md`): enough situations; enough Conversations; resting on clear Observations; score past the bar; a counter-test asked and answered with the evidence against under a bar; situational Observations carrying no weight; every quote checked; one model call arguing the other side found no better explanation (it can only block); safe; not rejected and its Pattern Type approved.

Safe means: no exclusion of its Pattern Type applies (the tagging step flags these from open Life Threads and recent Day Summaries; the catalog says whether evidence is ignored or counted but not shared), no Safeguard Event within an Admin-set time (start 14 days), and not a topic on the Admin-set ruled-out list unless the User raised it. A counter-test showing the behaviour doesn't happen in some kind of situation narrows the Pattern ("with seniors, not with friends") instead of failing it. Nothing is shared in this issue: a ready Pattern waits.

## Acceptance criteria

- [ ] A Pattern moves to ready only when all ten checks pass, and the log records which check last blocked it
- [ ] A Pattern of a draft Pattern Type never becomes ready, however strong its evidence
- [ ] A Pattern with no answered counter-test never becomes ready
- [ ] A counter-test showing it doesn't happen with some kind of person narrows the Pattern, and the narrowing is saved
- [ ] The other-side model call runs only when the other checks pass, and its "better explanation" answer blocks; a failed call blocks
- [ ] An active exclusion stops scoring or sharing as its Pattern Type says
- [ ] A Safeguard Event within the Admin-set time blocks ready
- [ ] A ruled-out topic blocks unless the User raised it; Admins edit the list
- [ ] A ready Pattern returns to suspected when evidence against arrives
- [ ] The gate is a pure function with tests for each check; the other-side prompt, model and thinking switch are Platform Settings
- [ ] Admins see how many Patterns a User has ready, never their content
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `04-explorations-and-the-agenda.md`

## Comments
