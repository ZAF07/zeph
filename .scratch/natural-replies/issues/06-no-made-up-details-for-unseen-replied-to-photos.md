# 06 — Zeph doesn't make up details of a replied-to photo it can't see

Status: ready-for-agent
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

- [ ] The seeded `response_prompt` has the line, worded plainly.
- [ ] The migration reloads `response_prompt` from the seed; no User data touched.
- [ ] Tests: the migration (like the one for 0077), and the Reply's instructions include the line (fake chat model); all Python checks pass.
- [ ] `/run`: in a worktree, reply to a photo with a caption only (real chat model) and see that Zeph's reply describes nothing beyond the caption.
- [ ] `docs/message-pipeline/README.md` decision 20 note mentions it.

## Blocked by

None - can start immediately.

## Comments
