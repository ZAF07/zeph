# 05 — Send a Shared Photo back

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

The Companion can now and then send a User's own Shared Photo back, the way a friend brings up an old memory.

- The reply sees descriptions of the User's relevant Shared Photos, picked the same way relevant Memory Items are, so it can bring them up in words too.
- The reply is offered a `send_photo` tool when the User has Shared Photos in use. It sends only that User's own Shared Photos, at most one per reply, after the text (like stickers), using Telegram's file id.
- The tool's description is an Admin-managed setting: use it rarely and never when the User is struggling.
- If Telegram refuses the photo, the text reply still goes out and the error is logged.

## Acceptance criteria

- [ ] The reply can mention a relevant Shared Photo and send it back, at most one per reply
- [ ] A Shared Photo of another User can never be sent, even if the model asks for it
- [ ] With User Memory off, no Shared Photos are shown to the reply and the tool isn't offered
- [ ] A failed send still delivers the text
- [ ] The tool description is editable on the admin Prompts page
- [ ] Seam 1 tests cover sending, the one-per-reply rule, other Users' photos and failure; adapter test for Telegram send photo
- [ ] A Persona Eval: a struggling User with Shared Photos gets no photo sent back (`make eval`)
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/04-shared-photos.md`
