# 02 — Look at a photo again with ask_about_photo

Status: completed

## Parent

`.scratch/photos/PRD.md`

## What to build

When the description can't answer a follow-up ("what colour is the pot?"), the Companion looks at the photo again.

- The reply is offered an `ask_about_photo` tool when the Conversation has viewed photos. It takes a photo from this Conversation and a question; the photo service downloads it from Telegram and answers in text with the same retries.
- The tool's description is an Admin-managed setting and says to use it only when the description can't answer.
- A failed look returns a plain "couldn't look again" answer to the reply, never an error.

## Acceptance criteria

- [x] A follow-up question about an earlier photo in the Conversation leads to a look with that question, and the answer reaches the reply
- [x] The tool isn't offered when the Conversation has no viewed photos
- [x] A failure is retried, then reported to the reply in plain words
- [x] The tool description is editable on the admin Prompts page
- [x] Seam 1 tests cover the tool, the question passed and failure
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/01-companion-sees-a-photo.md`

## Comments

### 2026-11-13 — plan (branch `photos-02-ask-about-photo`)

- `ChannelPhoto` gains `viewed` (stored in the existing `photos` JSON, so no migration). The photo service sets it when the description worked; photos from before this change read as not viewed.
- `PhotoService.read_message` replaces `message_text` and returns the text and the photo with `viewed` set. `PhotoService.ask(user, photo, question)` looks again with the description prompt plus the question, using the same retry loop and recording tokens in Usage.
- New `PhotoTools.offer(user, conversation)` gives the reply an `ask_about_photo` tool (photo number + question) listing the Conversation's viewed photos; none when there are none. A failed look, unknown number or missing question returns plain words.
- New setting `ask_about_photo_tool_description`; a core service can name extra prompts, so the Photo viewing card on the Prompts page shows it under the prompt.

### 2026-11-13 — evidence

- `make check` (after review fixes): ruff, ruff format, mypy pass; pytest 415 passed; web lint, prettier, typecheck pass; vitest 291 passed.
- Seam 1 `tests/test_photos.py` (11 new): a follow-up question looks again at the right photo with the description prompt plus the question, and the answer reaches the reply; the tool lists the Conversation's viewed photos by number under the Admin description; picks the photo by its number; not offered with no photos or only a failed photo; a failed look is retried `photo_retry_count` times, logged "Could not look at a photo again" and the reply is told in plain words; unknown number or blank question are said plainly with no look; a look puts its tokens into Usage; an edited description is offered and the Photo viewing card lists it. Vitest: the card shows the extra prompt and saves it with the prompt and model.
- `/run` on the existing install (`make restart`): `ask_about_photo_tool_description` was added on start. Owner's open Conversation moved back past the quiet gap, so a text with no photos started a new one; the reply said honestly it had no photo. The real Telegram photo (to-do list) sent with no caption: described and saved with `"viewed": true`. Follow-up "is the writing slanted left or right, anything doodled in the margin?" (not in the description) got "Slants slightly right. And no doodles"; calling the real photo service's `ask` in the backend container with the same file id and question gave "slanted to the right. Nothing is drawn in the margin" (real Telegram download + DeepSeek). Failure: a viewed photo with a broken file id added to the Conversation, then "in the bike photo… what brand name?": logs "Could not look at a photo again (try 1/2/3 of 3)", reply "I tried to zoom in on it again and couldn't…". Admin Prompts page (Playwright, signed-in Admin): Photo viewing card shows "ask_about_photo tool description" under the prompt; edit, save, reload kept it; original restored; no page errors. Test user, test message removed.
- Not run: `make eval` (no Eval in this issue's criteria; the reply prompt and Persona didn't change).

### Decisions

- `viewed` lives on the saved photo (`ChannelPhoto`, inside the existing `photos` JSON), so no migration. Photos saved before this change read as not viewed, so the tool isn't offered for them.
- Looking again uses the description prompt followed by the question, so its rules (no secrets, no guesses at who people are) still apply; no separate question prompt setting.
- The tool lists photos with their message text, cut at 300 characters, so the model can tell them apart. Notes left on issues 03 (album photos need their own lines) and 07 (`viewed` must mean "the reply saw it").
- A core service can name extra prompt settings; the Photo viewing card shows the tool description that way, ready for `send_photo` in issue 05.


## Completion

- Completed: 2026-11-13
- Commit: <to be filled in after merge>
