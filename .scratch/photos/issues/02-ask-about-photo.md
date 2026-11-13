# 02 — Look at a photo again with ask_about_photo

Status: in-progress

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

## Comments

### 2026-11-13 — plan (branch `photos-02-ask-about-photo`)

- `ChannelPhoto` gains `viewed` (stored in the existing `photos` JSON, so no migration). The photo service sets it when the description worked; photos from before this change read as not viewed.
- `PhotoService.read_message` replaces `message_text` and returns the text and the photo with `viewed` set. `PhotoService.ask(user, photo, question)` looks again with the description prompt plus the question, using the same retry loop and recording tokens in Usage.
- New `PhotoTools.offer(user, conversation)` gives the reply an `ask_about_photo` tool (photo number + question) listing the Conversation's viewed photos; none when there are none. A failed look, unknown number or missing question returns plain words.
- New setting `ask_about_photo_tool_description`; a core service can name extra prompts, so the Photo viewing card on the Prompts page shows it under the prompt.
