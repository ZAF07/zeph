# 07 — Photo Viewing as a Feature

Status: completed

## Parent

`.scratch/photos/PRD.md`

## What to build

Photo Viewing joins the Feature list, with the User's own switch (on by default) as well as the Admin switches for everyone and per User.

- Users switch it on the Dashboard (with Admin-managed explanation text: "When off, Zeph won't look at or remember your photos. Every photo is still checked for safety…") and in chat through a new settings tool (part of Settings in Chat).
- When it doesn't work for a User, every photo is still described, but only for the Safeguard. The reply and saved message get only the caption and an Admin-managed "not viewed" note, so the Companion says plainly it didn't look at the photo. `ask_about_photo` and `send_photo` aren't offered, no Shared Photos are kept or used, and existing ones aren't deleted.
- The switch shows "Not available on your account" when the Admin side has it off.

## Acceptance criteria

- [x] With Photo Viewing off (by the User, by an Admin, or for everyone), the reply answers the caption and says it didn't view the photo, and nothing is kept or sent back
- [x] A worrying photo with no caption still gets the Crisis Reply with Photo Viewing off
- [x] Existing Shared Photos aren't used while off and come back when on again
- [x] Users switch it on the Dashboard with the explanation text, and in chat ("stop looking at my photos") while Settings in Chat works
- [x] It shows on the admin Features page and per-User panel
- [x] Seam 1 tests cover each off case and the safety check; seam 3 tests cover the switch and text; a Persona Eval checks the off reply is honest; a Settings Eval case in `evals/cases/settings.yaml` checks "stop looking at my photos" calls the Photo Viewing tool (`make eval`)
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/04-shared-photos.md`
- `.scratch/features/issues/04-user-memory-and-check-ins-features.md`
- `.scratch/features/issues/05-settings-in-chat-feature.md`

## Comments

### 2026-11-13 — note from issue 02

- `ChannelPhoto.viewed` is set by `PhotoService.read_message` as "it was described". With Photo Viewing off the photo is still described for the Safeguard, so set `viewed` only when the reply saw the description; otherwise `ask_about_photo` would be offered for photos the User didn't let the Companion view.

### 2026-11-13 — plan (branch `photos-07-photo-viewing-feature`)

- `Feature.PHOTO_VIEWING` with the User's own switch: new `users.photo_viewing_enabled` (migration 0021, default true), `ChatSetting.PHOTO_VIEWING`, `PreferenceChanges.photo_viewing_enabled`; the Admin side blocks changes like User Memory.
- New settings: `photo_viewing_off_note` (reply note) and `photo_viewing_explanation` (Dashboard text). Migration 0021 also reloads `reply_settings_instructions`, which now names Photo Viewing.
- `PhotoService.read_message` still describes every photo. When Photo Viewing doesn't work, the reply and saved message get only "[photo you didn't look at. note] caption", photos aren't marked viewed and keep no description, and the turn carries a separate Safeguard text with the descriptions. The Safeguard reads that text for the newest message.
- Off also means: no `ask_about_photo`, memory retrieval leaves out Shared Photos (so no `send_photo`), conversation end keeps none, Check-ins see none (so no look-back Kind). Nothing is deleted; the Dashboard still lists and deletes them.
- Chat tool `turn_photo_viewing_on_or_off`, under Settings in Chat.
- Dashboard: `GET/PATCH /api/me` gain `photo_viewing_enabled` / `photo_viewing_available`; platform content gains `photo_viewing_explanation`; a Photo Viewing section on Account & privacy under User Memory (not in the design file, so it copies the User Memory section). Admin text fields on the Settings page.

### 2026-11-13: implemented, reviewed and verified

Done and verified: every acceptance criterion.

`make check` passed on the final code. Python: 530 passed. Web: 305 passed. ruff, ruff format, mypy, eslint, prettier and tsc were clean.

Full `make eval`: 56 of 57.
- Safeguard 32/32, Persona 23/23, Knowledge 8/8, Photo descriptions 1/1, Settings 13/14.
- The new cases passed:
  - `photo-viewing-off`, judged on `honest_when_photo_not_viewed`.
  - `photos-off` ("stop looking at my photos" called `turn_photo_viewing_on_or_off`).
  - `everyday-photos` (no tool called).
- The one fail, `moved-to-london`, is an existing flake. Zeph asked "is that right?" instead of calling the tool.
  - It passed 3 of 4 reruns on this branch.
  - It also passed only 3 of 4 on `main`, with the same failing reply.
  - So this change didn't cause it.

Live check (`/run`): the worktree stack was rebuilt from this branch and ran migration 0021. I signed in with Playwright as a temporary Clerk test Admin.

The Companion side used a probe inside the backend container. The probe ran the real app (`build_production_app`) on the worktree database, with the real DeepSeek chat model and photo viewer and the real LangGraph checkpointer. Only the Telegram channel was swapped, for a recorder that serves the Eval test images. Nothing went to Telegram.
- On: the weekend list photo with a caption was described. The reply named the list's items, and the saved message kept the description with `viewed: true`.
- Turned off with the Account & privacy switch (Playwright click). The same photo got:
  - Reply: "I can't see photos at the moment — photo viewing is turned off, so I didn't look at this one. What's on the plan?"
  - The Safeguard's newest line still held the full description.
  - The saved message held only the off marker and the caption: `viewed: false`, `description: ""`.
- Off, the goodbye note photo with no caption got the Crisis Reply, and a `suicide_or_self_harm` Safeguard Event was recorded.
- Chat, real model:
  - "it's fine, you can look at my photos again" turned it on, with a `photo_viewing` changed-in-chat mark.
  - "actually stop looking at my photos" turned it off.
- I added a Shared Photo (the house drawing) and checked it in fresh Conversations. I moved times back past the quiet gap to start each one.
  - On: the reply saw the photo and was offered `send_photo`. It answered "Yeah, the red house with the yellow sun in the corner — green door right in the middle."
  - Off: the reply didn't see it and `send_photo` wasn't offered.
  - Within one Conversation, the model kept its own earlier "I don't remember" even after Photo Viewing came back on. That is the model following its history, not the switch: the probe showed the photo was in the reply's instructions.
- Admin:
  - The Features page lists "Photo Viewing · On for everyone" with its description.
  - The Settings page shows the "Photo Viewing off" note and Photo Viewing explanation fields with their seeded text.
  - In the per-User panel, Photo Viewing first read "Off: the User turned it off". After clicking Off it read "Off: turned off for this User", with who and when.
- Account & privacy with the Admin side off: the switch was disabled and read "Not available on your account", above the explanation.
- In chat, "please look at my photos again" got "photo viewing isn't available on your account…", and nothing changed.
- At 390px there was no sideways scroll (scrollWidth 390). No page errors, and no tracebacks or errors in the backend logs.
- Clean-up: deleted the Clerk test user and its row. I confirmed 0 rows left for its Telegram link, Conversations, Shared Photo and Safeguard Event, and removed the probe files from the container.

Decisions:
- With Photo Viewing off, every photo is still described (up to the album cap) and goes only to the Safeguard. To make that work:
  - The turn carries `safeguard_text`.
  - `Safeguard.assess(newest_text=…)` swaps it in for the newest message only.
  - On later turns the Safeguard sees the off marker, because nothing about the photo is kept.
- The reply reads "[photo you didn't look at. <photo_viewing_off_note>] caption", with "photo N" in an album.
  - A photo that also failed to download reads the same way to the reply. The Safeguard text still has the "didn't come through" marker.
  - The album's "N more photos you didn't look at" note is left out while off. It tells Zeph to say it looked at the first few, which would be wrong.
- Off also means:
  - No `ask_about_photo`, even for photos viewed earlier in the Conversation.
  - Memory retrieval leaves out Shared Photos, so there is no `send_photo`.
  - Conversation end keeps no photos.
  - Check-ins see no Shared Photos, so the look-back Kind isn't offered.
  - Nothing is deleted, and the Dashboard still lists and deletes Shared Photos.
- The Dashboard switch sits on Account & privacy under User Memory. It isn't in the design file, so it copies the User Memory section's look ("Look at my photos").
- The two new Admin texts (`photo_viewing_off_note`, `photo_viewing_explanation`) sit with the other photo and Dashboard texts on the Settings page.
- Migration 0021 deletes the stored `reply_settings_instructions` row so the new seed loads. Admins who edited it get the new wording that names Photo Viewing.

Caveats, left for later:
- A Check-in that already sent a Shared Photo still puts that photo's description into the Conversation a reply starts, even if Photo Viewing was turned off in between. It is part of what Zeph already said.
- `PhotoViewingSetting.tsx` repeats `UserMemorySetting.tsx`. `_turn_photo_viewing_on_or_off` repeats the User Memory tool. With two of each, the copy is easier to read than a shared helper.
- The `moved-to-london` Settings Eval is flaky on `main` too.

Review (`/code-review`):
- Standards: no hard violations.
  - Fixed: the off note is now passed to `photo_marker` by keyword.
  - Left: the judgement calls above (duplication, the thin `PhotoService.viewing_works_for`, `""` for none in `TurnState`, which matches how `sticker_id` is stored).
- Spec: no missing criteria. It raised the Check-in edge case, the album count while off and the Safeguard seeing the description only on the turn the photo arrives. All three are recorded above as decisions or caveats.

Evidence:
- Seam 1 and seam 2: `tests/test_photo_viewing.py`, 23 tests.
  - The off reply and the Safeguard text, each for the User, an Admin and everyone.
  - The saved message, albums, and the Crisis Reply when off.
  - No `ask_about_photo`; Shared Photos not used, then back.
  - Conversation end keeps none; no look-back Check-in.
  - The Dashboard API switch, explanation and 403.
  - The Features page and panel.
  - The chat tool, including not available and Settings in Chat off.
  - Migration 0021.
- Also: `tests/test_features.py`, `tests/test_settings_via_chat.py`, `tests/test_admin_settings.py`, `tests/test_onboarding.py` and `tests/test_eval_helpers.py`.
- Seam 3: `AccountSettings.test.tsx` (switch, explanation, not available, changed in chat, save failure) and `PlatformSettingsForm.test.tsx` (the two texts).
- Seam 4: `evals/cases/persona.yaml` (`photo-viewing-off`) and `evals/cases/settings.yaml` (`photos-off`, `everyday-photos`).

## Completion

- Completed: 2026-11-13
- Commit: a1aa137 "Photos issue 07: Photo Viewing is a Feature with the User's own switch", review fix ed5d16d "Photos issue 07 review fix: pass the Photo Viewing off note to photo_marker by keyword", archive ae8ad5b "Photos issue 07 done: archive issue with test, run, eval and review evidence; glossary says Photo Viewing is a Feature with the User's own switch" (merged from `photos-07-photo-viewing-feature` in 72d2ea9 "Merge photos issue 07: Photo Viewing is a Feature with the User's own switch…"). `make check` was green on the branch rebased onto e10e3e5: Python 534 passed, web 305 passed. The last rebase, onto the issue 24 grilling, changed only docs (`.scratch/`, `CONTEXT.md`), and the merge's tree is identical to the branch tip.
