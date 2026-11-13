# 30 — Personal Stickers: the Companion replies in a User's own stickers

Status: completed

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

- [x] Personal Stickers Feature exists, off for everyone by default, and works only when Stickers works
- [x] At Conversation end, meaningful stickers are kept with a moment-only note; meaningless ones aren't; the per-User cap drops the one used longest ago
- [x] With the Feature off, nothing is kept or sent, and nothing is deleted
- [x] Replies can send one of the User's Personal Stickers (listed first, as theirs) or a global sticker; at most one; never in the Crisis Reply
- [x] Users see and remove their Personal Stickers on the Dashboard; Admins see a count only
- [x] Delete My Data and Account Deletion remove them
- [x] Tests at seams 1 and 3; `make check` passes
- [x] Verified in the running app via `/run`

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

**2026-11-13 — done.** What changed and the evidence:
- Feature: `Feature.PERSONAL_STICKERS` in `core/features.py`, off by default (`on_by_default=False`), and it doesn't work while Stickers doesn't (`needs_stickers`, reason `stickers_off`). It isn't named in the reply's "not available" note. Tests: `test_personal_stickers_is_a_feature_off_for_everyone_to_start`, `test_personal_stickers_works_only_when_stickers_works`.
- Keeping: the sticker a User sends is saved on its message (`conversation_messages.sticker`, migration 0022). At Conversation end, `PersonalStickerKeeper` (`core/personal_stickers.py`) makes its own model call (Admin-editable prompt and model on the Prompts page, "Personal Sticker keeping"). It runs whatever User Memory says and before User Memory processing; a failure is logged and doesn't block processing. Picks are checked. A sticker kept again gets its new note. The cap is `personal_stickers_limit` (30, Platform settings), and the one used longest ago goes first. A sticker's last use never moves back. Tests: kept with note, kept with User Memory off, bad picks skipped, note sharpened, no call without stickers, kept even if in the Sticker Library, cap drops oldest use, Feature off keeps nothing and deletes nothing, Stickers off for the User keeps nothing, the Companion's send counts as the last use.
- Sending: `send_sticker` lists theirs first as "(theirs)", then library stickers with a note not already theirs; one per reply; never in the Crisis Reply. `sticker_tool_description` is now Admin-editable (Prompts page, Response composition) and says to prefer theirs; migration 0022 reloads it. Tests: listed first and sent, Feature off offers only library stickers, a reply of just their sticker, only one per reply, Crisis Reply has none.
- Seeing and deleting: "Your stickers" on Account & privacy (image or emoji, note, remove; "Not available on your account" when off, still listed). The per-User Features panel shows only "Personal Stickers kept for <User>: N". Delete My Data removes them (`users.delete_data`), Account Deletion through the cascading foreign key; Message Retention leaves them. Tests: `tests/test_data_deletion.py` (personal_stickers in every-kind-of-data), `test_message_retention_keeps_personal_stickers`, Dashboard API list/image/remove/404, `personal_stickers_available` on `/api/me`, count on the panel; Vitest `PersonalStickersSection.test.tsx`, `UserFeaturesPanel.test.tsx`, `AccountSettings.test.tsx`.
- Checks: `make check` passed: ruff, ruff format, mypy (95 files), pytest 556 passed, ESLint, Prettier, tsc, Vitest 314 passed.
- `/run` (worktree stack, plain User, fake Telegram link, real DeepSeek): a sticker message is saved with its sticker; at Conversation end 😂 sent after "I dropped my toast butter side down" was kept as "for laughing along at a small everyday mishap", and 🫥 sent with no clear meaning was skipped; after the review fixes 🎉 sent about a new job was kept as "for celebrating good news like a new job or a night out". The Account & privacy section showed it at 1280px and 390px, showed "Not available on your account" with the Feature off and still listed it, and Remove emptied it (0 rows left). The Admin per-User panel showed "Personal Stickers: Off: turned off for everyone" and "Personal Stickers kept for Run check: 1". The Prompts page lists "Personal Sticker keeping" and the "send_sticker tool description"; Platform settings has "Most Personal Stickers per User"; migration at 0022.
- Code review (Standards and Spec): no hard Standards breaches. Fixed: a Personal Sticker's last use could move back when the Companion sent it after the User in the same Conversation (red/green test); the Stickers dependency was named as if any Feature could need any other (now `needs_stickers`); `picked_notes` renamed `notes_for_valid_picks`; the limit key inlined like its neighbours. Also fixed during `/run`: messages without a sticker stored a JSON null instead of SQL NULL (`JSONB(none_as_null=True)`, red/green test). Left as is: a type alias for "library or personal sticker", a 404 helper, a separate count endpoint.

Caveats:
- Sending one of their stickers back couldn't be shown end to end from a worktree: the fake chat makes Telegram refuse the typing action before a reply is written. It is covered at seam 1.
- Until issue 24 lands, an Admin's sticker still goes to the Sticker Library and isn't chat, so Admins' stickers don't become Personal Stickers yet. Once 24 saves them as chat, they are picked up with no change here.
- No design was added to `docs/design/`; the section follows the Photo Viewing section's layout.
- If User Memory processing fails and is retried, the keeping call runs again (harmless, one more model call).

## Completion

- Completed: 2026-11-13
- Commit: c872d35 (merge into main): "Merge MVP issue 30: Personal Stickers is a Feature, off for everyone to start, that works only while Stickers does; …"
  - e0ef800 "MVP issue 30: Personal Stickers, the Companion replies in a User's own stickers"
  - 16bdd93 "MVP issue 30 review fixes: a Personal Sticker's last use never moves back, and the Stickers dependency says what it does"
  - 64760a6 "MVP issue 30 done: archive issue with test, run and review evidence; glossary says a Personal Sticker is used when either side sends it"
