# 06 — Zeph doesn't make up details of a replied-to photo it can't see

Status: completed
Track: B
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/archive/PRD.md` (follow-up from issue 04)

## What to build

When a User replies to an old photo, Zeph gets only its caption, not the image: the Replied-to Text is read from the chat update, never from our saved messages, and the photo is not looked at again. In the issue 04 `/run`, a reply "so cute" to an old photo captioned "my cat" got "the ear tuft is doing a lot of work", a detail Zeph made up.

- Add a line to the Reply's `response_prompt` in `src/companion/seed/platform_settings.yaml`: when the User replies to a photo or sticker you can't see, don't describe what's in it; go by the caption and what they say, or ask.
- Reload `response_prompt` from the seed with a migration (next free number; 0077 did the same by deleting the stored row).
- Not in scope: downloading and describing the replied-to photo with Photo Viewing. It would cost a model call per such reply. Revisit if replies to photos turn out common.

## Acceptance criteria

- [x] The seeded `response_prompt` has the line, worded plainly.
- [x] The migration reloads `response_prompt` from the seed; no User data touched.
- [x] Tests: the migration (like the one for 0077), and the Reply's instructions include the line (fake chat model); all Python checks pass.
- [x] `/run`: in a worktree, reply to a photo with a caption only (real chat model) and see that Zeph's reply describes nothing beyond the caption.
- [x] `docs/message-pipeline/README.md` decision 20 note mentions it.

## Blocked by

None - can start immediately.

## Comments

**Done, 24 Nov 2026.** Evidence per criterion:

- Prompt line: `response_prompt` in `src/companion/seed/platform_settings.yaml` ends with "When they reply to a photo or sticker you can't see, don't describe what's in it. Go by its caption and what they say, or ask them about it."
- Migration: `0078_unseen_photos_prompt.py` deletes only the stored `response_prompt` row; the seed refills it on start. On the worktree stack it applied (`alembic_version` 0078) and the stored prompt then had the new line.
- Tests: `test_the_migration_reloads_the_response_prompt_from_the_seed` and `test_the_migration_keeps_the_users_messages` (real Postgres, down to 0077 and back up); `test_the_reply_is_told_not_to_describe_a_replied_to_photo_it_cant_see` (fake chat model, Reply call's instructions). All three red before the change. `ruff check`, `ruff format --check`, `mypy` clean; `pytest` 1650 passed.
- `/run` in the worktree (real backend app and Postgres, real DeepSeek chat model, chat channel swapped for a recording one), a text replying to a 20-day-old photo of the User's own:
  - "so cute" to a photo captioned "my cat": "Ha, that little face. What's their name?" and, run again, "Genuinely, that face. What's the name?"
  - "look how big he got" to a photo with no caption: "Oh he's a proper little man now. Look at that face. / How old is he in this one?"
  - No reply describes anything beyond the caption and the User's words; it asks instead.
- Docs: decision 20 in `docs/message-pipeline/README.md` has a "Built (23 Nov 2026)" note naming the line and migration 0078.
- Caveat: like 0077, the migration replaces an Admin-edited `response_prompt` with the seed.

## Completion

- Completed: 2026-11-24
- Commit: <to be filled in after merge>
