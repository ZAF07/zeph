# 30 — Personal Stickers: the Companion replies in a User's own stickers

Status: in-progress

## Parent

`.scratch/mvp/PRD.md`. Split out of `issues/24-admin-stickers-in-chat.md` during its grilling on 2026-11-13. See **Personal Stickers** in `CONTEXT.md`.

## Today

Stickers a User sends are read through their emoji and answered, but never kept. The Companion only sends stickers from the shared Sticker Library.

## What to build

### The Feature

- New Feature **Personal Stickers**, switched by Admins for everyone and per User like the others. It's a higher-plan extra for later, so it's **off for everyone by default** (seed/migration).
- It works only when **Stickers** also works for the User.
- When it doesn't work: no new Personal Stickers are kept and none are sent (global stickers only). Existing ones aren't deleted.
- Users have no switch of their own; it shows "Not available on your account" when off.

### Keeping stickers

- When a Conversation ends (the same place Shared Photos are picked), the Companion looks at the stickers the User sent in it and keeps the ones whose meaning is clear from how they were used.
- For each one it writes a "when to use" note from the emoji and the chat around it, with no vision call. The note describes the moment, never the User (e.g. "for laughing at a small mishap", not "when Sam laughs at being clumsy").
- It skips stickers with no clear meaning. Sending one it already kept can sharpen its note.
- It's kept even if the same sticker is in the Sticker Library.
- At most N per User (new Admin setting, e.g. 30). When full, it drops the one used longest ago.
- Personal Stickers are **not User Memory**: User Memory on/off doesn't affect them, and the Companion never brings them up as a memory or in a Check-in.

### Sending

- One `send_sticker` tool with one numbered list: the User's Personal Stickers first, marked "(theirs)", then global stickers that have a note. A sticker in both is listed once, as theirs, with its Personal note.
- The tool description (Admin-editable) says to prefer theirs when it fits. Still at most one per reply, rarely, and never in the Crisis Reply.

### Seeing and deleting

- Users see their Personal Stickers on the Dashboard (image and note) and can remove any one. This stays visible even when the Feature is off.
- Admins see only how many a User has, on the per-User panel.
- Delete My Data and Account Deletion remove them. Message Retention doesn't.

## Design

No design yet in `docs/design/`. Add the User page and the per-User count to the design first, or build a simple layout that follows the existing pages.

## Acceptance criteria

- [ ] Personal Stickers Feature exists, off for everyone by default, and works only when Stickers works
- [ ] At Conversation end, meaningful stickers are kept with a moment-only note; meaningless ones aren't; the per-User cap drops the one used longest ago
- [ ] With the Feature off, nothing is kept or sent, and nothing is deleted
- [ ] Replies can send one of the User's Personal Stickers (listed first, as theirs) or a global sticker; at most one; never in the Crisis Reply
- [ ] Users see and remove their Personal Stickers on the Dashboard; Admins see a count only
- [ ] Delete My Data and Account Deletion remove them
- [ ] Tests at seams 1 and 3; `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/24-admin-stickers-in-chat.md` (same sticker code; Admin stickers must be answered before they can become Personal Stickers)

## Comments

**2026-11-13 — grilled (as part of issue 24).** Decisions:
- Named "Personal Stickers", because "Album" already means several photos sent at once.
- Not User Memory: stickers are how the Companion talks, not something it remembers about the User.
- Its own Feature, off by default, because it's for a higher plan after the MVP.
- Kept even when also in the Sticker Library, so the Companion knows what is the User's.

**2026-11-13 — started on branch `mvp-30-personal-stickers`.** Issue 24 is still in progress in another worktree; its block only matters for Admins' own stickers (today they go to the library and aren't saved as chat), so this goes ahead and is rebased onto main before merging. Plan:
- Messages keep the sticker: a User's sticker turn carries its `ChannelSticker`, saved in a new `conversation_messages.sticker` column, so it can be kept when the Conversation ends.
- New `personal_stickers` table (one row per User and sticker, with note, kept and last-used times), cascading on User delete; `users.delete_data` removes them too. Message Retention doesn't touch them.
- Feature `PERSONAL_STICKERS`: each Feature gets a code default, and this one is off for everyone. It needs Stickers: when Stickers doesn't work it doesn't either (new reason "stickers_off"). It isn't named in the reply's "not available" note, since Users don't ask for it.
- Keeping: a new core `PersonalStickerKeeper` makes its own model call (new prompt and model settings, a Prompts page service) when a Conversation ends, separate from post-conversation processing, so User Memory doesn't affect it. It runs only when the Feature works and the User sent stickers. Picks are checked; a pick of one already kept updates its note; any kept sticker the User sent again counts as used. Then the User's stickers over `personal_stickers_limit` (30, Platform settings) are dropped, oldest use first.
- Sending: `send_sticker` lists theirs first "(theirs)", then library stickers with a note not already theirs. Delivery finds the sticker in the library or the User's own and marks theirs as used. `sticker_tool_description` becomes Admin-editable (Prompts page, Response composition) and says to prefer theirs; migration 0022 reloads it.
- Dashboard: "Your stickers" section on Account & privacy (image, note, remove; "Not available on your account" when off). Admin per-User Features panel shows the count.
