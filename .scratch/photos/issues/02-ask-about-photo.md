# 02 — Look at a photo again with ask_about_photo

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

When the description can't answer a follow-up ("what colour is the pot?"), the Companion looks at the photo again.

- The reply is offered an `ask_about_photo` tool when the Conversation has viewed photos. It takes a photo from this Conversation and a question; the photo service downloads it from Telegram and answers in text with the same retries.
- The tool's description is an Admin-managed setting and says to use it only when the description can't answer.
- A failed look returns a plain "couldn't look again" answer to the reply, never an error.

## Acceptance criteria

- [ ] A follow-up question about an earlier photo in the Conversation leads to a look with that question, and the answer reaches the reply
- [ ] The tool isn't offered when the Conversation has no viewed photos
- [ ] A failure is retried, then reported to the reply in plain words
- [ ] The tool description is editable on the admin Prompts page
- [ ] Seam 1 tests cover the tool, the question passed and failure
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/01-companion-sees-a-photo.md`
