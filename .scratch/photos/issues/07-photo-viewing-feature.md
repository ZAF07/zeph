# 07 — Photo Viewing as a Feature

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

Photo Viewing joins the Feature list, with the User's own switch (on by default) as well as the Admin switches for everyone and per User.

- Users switch it on the Dashboard (with Admin-managed explanation text: "When off, Zeph won't look at or remember your photos. Every photo is still checked for safety…") and in chat through a new settings tool (part of Settings in Chat).
- When it doesn't work for a User, every photo is still described, but only for the Safeguard. The reply and saved message get only the caption and an Admin-managed "not viewed" note, so the Companion says plainly it didn't look at the photo. `ask_about_photo` and `send_photo` aren't offered, no Shared Photos are kept or used, and existing ones aren't deleted.
- The switch shows "Not available on your account" when the Admin side has it off.

## Acceptance criteria

- [ ] With Photo Viewing off (by the User, by an Admin, or for everyone), the reply answers the caption and says it didn't view the photo, and nothing is kept or sent back
- [ ] A worrying photo with no caption still gets the Crisis Reply with Photo Viewing off
- [ ] Existing Shared Photos aren't used while off and come back when on again
- [ ] Users switch it on the Dashboard with the explanation text, and in chat ("stop looking at my photos") while Settings in Chat works
- [ ] It shows on the admin Features page and per-User panel
- [ ] Seam 1 tests cover each off case and the safety check; seam 3 tests cover the switch and text; a Persona Eval checks the off reply is honest; a Settings Eval case in `evals/cases/settings.yaml` checks "stop looking at my photos" calls the Photo Viewing tool (`make eval`)
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/04-shared-photos.md`
- `.scratch/features/issues/04-user-memory-and-check-ins-features.md`
- `.scratch/features/issues/05-settings-in-chat-feature.md`
