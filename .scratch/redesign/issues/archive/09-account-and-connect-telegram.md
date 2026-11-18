# 09 — Redesign: Account & privacy and Connect Telegram

Status: completed

Lane: A. README slices: 5 and 6.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Account & privacy** (`/account`) to `Account` and `M-Account`. Same settings, Delete My Data and Account Deletion behaviour as now. The confirm steps use the shared confirm part.
- **Connect Telegram** (`/connect-telegram`) to `ConnectTelegram` and `M-ConnectTelegram`: the main card plus every other state drawn under its annotations (waiting, connected, expired, and so on), each matched to the existing Telegram Connection and Connection Token states. No QR code on a phone; the button is the action.
- Fixture data goes in the account and telegram fixture files.

If a drawn Telegram state has no matching state today, or a current state isn't drawn, stop and ask.

Refs: `Account`, `M-Account`, `ConnectTelegram`, `M-ConnectTelegram`.

## Acceptance criteria

- [x] All four refs PASS. — Account and M-Account PASS. **ConnectTelegram and M-ConnectTelegram FAIL only because their baselines include the orange builder notes; Zaf chose on 2026-11-19 to leave the notes out of the page.** The part above the notes matches (see below).
- [x] Each Connect Telegram state shows its drawn design (test per state). — `TelegramConnectionCard.test.tsx`: ready, loading, waiting, connected, expired, linked elsewhere, couldn’t create.
- [x] Linking Telegram, settings and deletion work as before (`/run`, posting to the worktree's webhook). — see the /run notes below.

## Blocked by

- `.scratch/redesign/issues/02-shell.md`
- `.scratch/redesign/issues/03-shared-states.md`

## Rules for every redesign issue

- Read `web/design/README.md` in full, then every reference file named here at both widths, before coding. The README wins on look, copy and behaviour. Where it and this issue differ, stop and ask. Its "When to stop and ask" list applies.
- Build so the computed styles equal the reference's inline styles. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory. Use only the tokens (arbitrary values like `gap-[22px]` where no token exists).
- Never change anything in `web/design/` (`LIMIT`, masks, baselines, references), except the one image swap and baseline rebuild in issue 01.
- Own worktree (`make worktree-setup`), own branch, own PR. Run the pixel test with `BASE_URL=http://localhost:$WEB_PORT`, `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, and the two session files from issue 01's script.
- **Parallel work.** Two agents work at once. Put this issue's sample data in its own fixture file for its page area, and don't edit another area's file. Only issue 01 edits the theme, font, fixture switch and pixel-test setup. Only issue 02 edits the sidebar and menu. Only issue 08 edits the middleware. If you need a change in one of those, stop and ask.
- Use the shared state parts from issue 03 (empty, loading, error, saved, confirm) for every state this issue's pages show (from issue 04 on).
- Existing behaviour, API calls, Clerk logic and tests stay as they are. Update a test only where the markup it checks has changed.
- Before the PR: `git fetch origin && git rebase origin/main`, then re-run this issue's pixel test and checks.

## Done when (for every redesign issue)

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs. — the two ConnectTelegram refs are the accepted FAIL.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-18 — From issue 02: the `getPlatformContent` fixture lives in `web/src/lib/design-fixtures/shell.ts`. Only `ai_notice_short` (the sidebar line) and `message_retention_days: 30` are filled in. If this page shows the other fields, fill them from its reference there; it is the shared shell fixture, so mention it in the issue.

- 2026-11-18 — From issue 05: the `(user)` 880px column layout is gone (User pages now sit straight in `<main>`, as every reference draws). On a phone, the old Connect Telegram card printed a long Telegram username (`@maximiliana_featherstonehaugh_whittington_long`) 4px past the screen. Let long usernames wrap (Home uses `[overflow-wrap:anywhere]`). Time zone is set only on Account now: Zaf dropped it from Check-ins.

- 2026-11-18 — Decisions (Zaf, asked at start):
  - Delete my data / Delete my account use the shared `ConfirmDialog`, with no type-DELETE box. Words: data — "Delete my data?" / the Admin `delete_my_data_description` + " This can’t be undone." / "Keep my data" · "Delete my data". Account — "Delete your account?" / "Erases everything above plus your account. This can’t be undone." / "Keep my account" · "Permanently delete account".
  - Connect Telegram states (waiting, connected, expired) use the main card's box (padding 26/28, radius 16, panel bg), with the tile's title and text (minus the "Button:" sentence) and the named buttons in a row below: first cream pill, second outline pill. Tested per state; no pixel ref.
  - Undrawn Telegram states: loading → shared loading part; couldn't create link → shared error part with Try again; linked to another account → looks like expired (coral title), today's words, "Get a new link".
  - Account: drop the "You can also tell Zeph…" line; retention line is "Messages are otherwise kept for {N} days."; memory-off note, not-available text, sticker loading/empty/error, saved/failed notes use the shared parts.
- 2026-11-19 — The ConnectTelegram baselines include the orange builder notes ("Other states of this card", "Banner shown on Home until connected"). Zaf: leave the notes out of the page. ConnectTelegram and M-ConnectTelegram stay FAIL until the baselines are re-made without them; the part above the notes is checked separately.

- 2026-11-19 — Evidence (after rebasing on `origin/main` at `ddf5bb4`).

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3010`, `BASE_URL=http://localhost:3010`, sessions from `design-sessions.sh`):
```
PASS  Account                            0.03% differs, height 1503 vs 1503
PASS  M-Account                          0.07% differs, height 2275 vs 2275
FAIL  ConnectTelegram                    2.60% differs, height 800 vs 856
FAIL  M-ConnectTelegram                  2.16% differs, height 844 vs 1205
```
Only the part above the first builder note, compared with the same pixelmatch settings:
```
ConnectTelegram: top 413px, 1.48% differs   (all of it is the real QR code where the reference draws a "QR code" box, as on Onboarding)
M-ConnectTelegram: top 458px, 0.05% differs
```
Pages that share parts I changed still pass: Onboarding 0.12%, M-Onboarding 0.06%, Dashboard 0.01%, Dashboard--menu-folded 0.00%, M-Dashboard 0.01%, Memories and its five tabs ≤0.02%, M-Memories 0.05%.

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 91 files, 585 tests passed.

**/run with real data** (production web container, real User session):
- Connect Telegram: the ready card showed a real link (`@Zeph_07_bot`); at 390 the QR code is hidden and the phone line shows. Open in Telegram → waiting. The token was expired in the database → "I’ve pressed Start" → expired; Get a new link gave a new token. A `/start <token>` update was posted to `http://localhost:8010/telegram/webhook` (200) with the username `maximiliana_featherstonehaugh_whittington_long` → the page moved to connected on its own; the long username wraps, and at 390 the page width stays 390 (no sideways scroll). No page errors.
- Account: Save was locked until country and time zone were chosen (the test user had none, as before). A 52-character name, SG and Asia/Singapore were saved ("Saved." shown, database row matched). The photos switch saved `false`, then was turned back on. At 390 the page fits (width 390), and the long email wraps.
- Delete my data: dialog "Delete my data?" → Keep my data left the Telegram Connection in place (1 row); confirming removed it (0 rows) and showed "Your data has been deleted…".
- Delete account: dialog "Delete your account?" → Permanently delete account signed the user out to `/sign-in`, and the users row was gone.
- Not checked with real data: a sticker list. The test user has no Personal Stickers (and the feature was off for them). The list layout is covered by the Account pixel test on fixtures.

**Chosen myself / unsure (for Zaf to confirm).**
- The sticker remove button keeps today's label "Remove sticker 🤗" (or "with no emoji"), not the reference's "Remove sticker 1".
- A sticker with an emoji but no image shows the emoji at the drawn 11px in the dashed box (it was 36px). The reference only draws stickers with no emoji.
- Curly apostrophes are kept in fixed copy ("can’t", "you’d"), as on earlier pages. The fixture explanation text uses the reference's straight ones.
- Time zone shows "Singapore (GMT+8)" where the reference shows "Asia/Singapore", as on Onboarding.
- Gaps between the Telegram state text and its buttons (18px) and between buttons (8px) come from the Profile card and the confirm dialog; the states have no drawing of their own.
- The memory-off note on Account uses the shared `MemoryOffNotice` without its "Turn memory on" button (the switch beside it does that). `MemoryOffNotice`'s `onTurnOn` is now optional.
- The shared shell fixture (`design-fixtures/shell.ts`) now fills `user_memory_explanation`, `photo_viewing_explanation` and `delete_my_data_description` from `Account.html`.
- `LocationFields` has a new `inline` option so its two pickers wrap with the name and email fields, as drawn.

**Existing tests changed.**
- `AccountSettings.test.tsx`: the delete tests use the confirm dialog instead of typing DELETE (Zaf's decision). The data region is now named "Delete my data" (its heading). The "You can also tell Zeph…" test is removed (line dropped). The retention test checks the new line. "Saved" is now "Saved." (shared SavedNote).
- `TelegramConnectionCard.test.tsx`: the QR code's name is now "QR code that opens Zeph in Telegram", and it is checked to be hidden on a phone. The linked-elsewhere and couldn’t-create tests also check their look. New tests cover loading, waiting, connected and expired.

**Code review** (two sub-agents, standards and spec): no hard violations, and nothing missing or wrong against the spec. Fixed: one shared `panelCard` class for the card box, one word table for the two link-problem states, and no dummy turn-on handler. Answered, not changed: the 20px/24px stickers gap follows `<main>`'s own phone switch. The page-header eyebrow looks like `PageHero`'s, but the header has no illustration, so it is kept separate. The onboarding fixture's link is not reused because that is another area's file.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after the merge>
