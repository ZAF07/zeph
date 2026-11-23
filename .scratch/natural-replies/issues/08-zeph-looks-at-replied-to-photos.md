# 08 — Zeph looks at a photo the User replies to

Status: ready-for-agent
Track: B
Blocked by: None - can start immediately (goes with 06: its prompt line still covers a photo that can't be looked at)

## Parent

`.scratch/natural-replies/archive/PRD.md` (follow-up from issue 04)

## What to build

Today a reply to an old photo gives Zeph only the caption (issue 04). Zeph should look at the photo, as it does a new one.

- The Telegram adapter also reads the replied-to photo (largest size, as `parse_photo` does) into the Replied-to Text, as a `ChannelPhoto`.
- When a User's text replies to a photo, core describes it with the same Photo Viewing step as a new photo (`PhotoService.describe`: `photo_model`, `photo_description_prompt`, retries), when the text arrives, before the Safeguard.
- The description is kept in the saved Replied-to Text and shown in the note, e.g. `(replying to their own photo from 3 Nov 2026, "my cat", [photo: a grey cat asleep on a laptop]) so cute`.
- Same rules as a new photo: always described for the Safeguard; the Understanding, Reply Plan and Reply see the description only when Photo Viewing works for the User, otherwise only the caption and the "Photo Viewing off" note.
- A photo that can't be downloaded or looked at falls back to today's behaviour: caption only (and 06's prompt line applies).

## Limitations

- **Costs one photo-model call per reply to a photo**, counted in the User's usage. The same old photo replied to twice is looked at twice; no reuse of an earlier description.
- **Slower reply**: the look happens before the Safeguard, so a reply to a photo waits a few seconds more, like sending a photo does.
- **Telegram may not keep old files.** Telegram doesn't promise an old photo stays downloadable; when it doesn't, Zeph gets the caption only.
- **Too big to download**: a photo sent as a file over the bot download limit (20 MB) can't be looked at.
- **One photo only**: a reply points at one photo, even if it was part of an Album; the Album's other photos aren't looked at.
- **Photos only**: stickers stay as their emoji; videos, GIFs and files aren't looked at.
- **After Message Retention**: Zeph can look at a photo whose saved message we already deleted, because the photo comes from Telegram, not our database. It's the User pointing at it, so this is accepted; the new description is kept and deleted like any saved text.
- **Photo Viewing off**: the photo is still looked at for the Safeguard, so the model call still happens, as for a new photo.

## Acceptance criteria

- [ ] A text replying to a photo gets the photo's description in the Understanding, Reply Plan and Reply notes (fake photo viewer).
- [ ] With Photo Viewing off, only the Safeguard's transcript has the description; the others have the caption and the "Photo Viewing off" note.
- [ ] A photo that can't be downloaded or looked at falls back to the caption only, and the reply still goes out.
- [ ] The look's tokens count toward the User's usage, and it shows in the Model Call Log like a new photo's look.
- [ ] Delete My Data and Message Retention remove the description with the text (it is in the same row).
- [ ] Tests through the webhook (fake chat channel download, fake photo viewer), the Telegram adapter (helper in `tests/telegram_helpers.py` for a reply to a photo) and any migration; all Python checks pass.
- [ ] `/run`: in a worktree, reply to a real photo (one the bot can download) and see its description in the Model Call Log for the Understanding and Reply, and a reply that matches the photo.
- [ ] `docs/message-pipeline/README.md` decision 20 note and the Photo Viewing step say what is built, with these limitations.

## Notes

- No ADR: it's a behaviour that's easy to turn off or remove, not a hard-to-reverse choice.

## Blocked by

None - can start immediately.

## Comments
