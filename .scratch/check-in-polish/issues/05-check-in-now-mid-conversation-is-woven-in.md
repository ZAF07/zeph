# 05 — Check-in polish: Check in Now mid-Conversation is woven in

Status: ready-for-agent

Track: whichever agent finishes first (needs both tracks).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

Join Check in Now (04) with Woven-in Check-ins (02). When an Admin asks for a Check in Now for a User who is mid-Conversation, it is offered to the reply flow as a Woven-in Check-in instead of waiting for the Conversation to end.

- The reply flow's "is a Check-in due?" check counts a waiting Check in Now. For that User it goes past the Feature switch and the pause, matching 04.
- The "not struggling" code rule still applies.
- When woven in, the saved Check-in records the requesting Admin and is marked woven in. The request is cleared, and the next Due Time is "decided at + frequency gap".
- If no reply weaves it in, it goes out on its own once the Conversation ends, still as the Admin's Check in Now.

## Acceptance criteria

- [ ] A Check in Now for a User mid-Conversation is offered to the woven-in Check-in call and, when chosen, woven into the reply. It is logged as woven in and as asked for by that Admin (end-to-end test).
- [ ] It goes past the pause and the Feature switch, but never past "struggling".
- [ ] If not woven in, it is sent on its own after the Conversation ends, logged with the Admin.
- [ ] The request is cleared after either path, and the next Due Time is one gap after.
- [ ] All backend and web checks pass.
- [ ] Verified with `/run`: request a Check in Now while chatting through the webhook and see it woven into a reply.

## Blocked by

- `.scratch/check-in-polish/issues/02-woven-in-check-ins.md`
- `.scratch/check-in-polish/issues/04-check-in-now.md`

## Comments
