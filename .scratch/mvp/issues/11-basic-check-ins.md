# 11 — Basic Check-ins

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users can opt in to Check-ins, and the Companion messages them first. Adds a Check-ins step to onboarding (off by default; frequency and quiet hours when on) and the same settings on the preferences page. On each scheduler tick, the Check-in service finds Users who are due (opted in, frequency elapsed, outside quiet hours in their time zone) and sends a casual-hello Check-in written by the LLM. A User replying to a Check-in starts a normal Conversation. Check-in Kinds are seeded from data files (casual hello, follow-up, present-moment prompt, thought to reflect on); this slice uses only casual hello.

## Acceptance criteria

- [ ] Onboarding has a Check-ins step: off by default; frequency and quiet hours when turned on
- [ ] The preferences page lets the User change frequency and quiet hours, or turn Check-ins off
- [ ] A scheduler tick sends a casual-hello Check-in to Users who are due, and never during quiet hours in the User's time zone
- [ ] Each sent Check-in is recorded and the next due time is set
- [ ] A reply to a Check-in starts a Conversation that is handled like any other
- [ ] Check-in Kinds are seeded from data files
- [ ] Seam 2 tests with a fake clock cover: due → sent, quiet hours → not sent, time zone respected, Check-ins off → not sent, reply → Conversation
- [ ] Seam 3 tests cover the onboarding step and preferences settings
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/03-onboarding.md`
- `.scratch/mvp/issues/06-user-memory.md`
