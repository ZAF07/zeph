# 01 — Copy: Landing end to end

Status: completed

Lane: A. The tracer: every other issue builds on it.

## Parent

`.scratch/copy/PRD.md`

## What to build

The whole Copy path, proved on one page. An Admin opens the new Copy page (`/admin/copy`), sees a Landing tab with Landing's slots in page order, edits some, and saves. A signed-out visitor reloads `/` and sees the new words, with the design unchanged.

- Copy store kept apart from Platform Settings (ADR-0019), seeded from its own seed file in prestart: new slots added, edited slots keep their text, a slot's name, tab, order, max length and placeholders always follow the seed, and slots gone from the seed are removed.
- Public read of all Copy (no sign-in), Admin read of the Copy page (tabs, slots, last changed by and when) and Admin save of one tab.
- Tab save is all or nothing and turned away, with a reason per slot, for: empty text, over max length, a required placeholder missing, an unknown placeholder, a slot from another tab. Plain Users are refused.
- One small pure helper fills `{name}` placeholders. Plain text only: no markdown, links or HTML read from Copy.
- Landing reads every word from Copy, including its browser tab title and search description. The page code holds no default text. If Copy can't be read, Landing shows the normal error state.
- The Copy page is one page with tabs (only Landing for now). It has no reference file, so read `web/design/README.md` ("Building new UI") first and build it only from existing parts and token values: tabs as `MemoriesTabs` draws them, a text field per slot with name, placeholders and a counter as `FormEditor` draws it, and `CardSaveBar`. No new colours, sizes or gaps. Field errors show on the failing slot.
- The design fixture API client serves the seed Copy, and the Landing seed text matches the reference exactly.

## Acceptance criteria

- [x] Prestart seeds the Copy store; re-seeding keeps an Admin-edited slot's text and updates its name/max length/placeholders from the seed; a slot removed from the seed is gone.
- [x] Signed out, the public read returns every slot's key and latest text.
- [x] An Admin sees the Landing tab with slots in page order, each with name, text, max length, placeholders and last changed by/when.
- [x] A tab save applies all its changes; empty, too long, missing placeholder, unknown placeholder and other-tab slot each turn away the whole save with an error on that slot.
- [x] A plain User can't read the Copy page or save.
- [x] Landing (including tab title and description) shows only Copy text; no default text in web code.
- [x] Landing shows the normal error state when Copy can't be read.
- [x] Backend HTTP tests, Dashboard tests and placeholder helper tests cover the above; all Python and web checks pass.
- [x] The pixel test passes for the Landing refs at both widths.
- [x] `/run`: the Copy page at 1280 and 390 uses only existing parts and token values, checked by eye against `MemoriesTabs`, `FormEditor` and `CardSaveBar` on their own pages; screenshots at both widths.
- [x] `/run`: as an Admin, change the Landing main heading, reload signed-out `/` and see it; try a save over max length and see it turned away on that slot.

## Blocked by

- All of `.scratch/redesign/` completed.

## Comments

- 2026-11-19 — Done (branch `copy-01-landing`).
  - Backend: `copy_slots` table (migration 0062), `CopyRepository` port and `PostgresCopyRepository`, `CopyService` (`core/copy.py`), routes in `adapters/http/copy_api.py`: `GET /api/copy` (public, `{"texts": {key: text}}`), `GET /api/admin/copy`, `PUT /api/admin/copy/{tab}`. Seed `src/companion/seed/copy.yaml`, loaded by `seed_copy` in prestart. Copy is read from the database on every request (no in-process cache), so a save shows on the next load whichever process serves it.
  - Web: `lib/copy.ts` (`readCopy`, `fillPlaceholders`), `lib/server-copy.ts` (`loadCopy`, server-side, once per request), Landing and its sections take `copy`; `/` and `/pricing` show `SiteLoadFailed` when Copy can't be read; `generateMetadata` on `/` gives title and description from Copy. Copy page `/admin/copy` (`CopyEditor`, `CopyTabs`, `CopySlotField`), menu item "Copy" after Platform settings. `FormEditor` got an optional `maxLength` for the "n / max characters" count.
  - Server-side calls in Docker use `SERVER_API_URL` (set to `http://backend:8000` in `docker-compose.yml`); without it the browser's address is used.
  - Design fixtures: `design-fixtures/seed-copy.json` is the seed as JSON; `test_the_design_fixture_copy_is_the_seed_copy` keeps them equal.
  - Choices: headings drawn with a line break are two slots ("first line"/"second line"). The `/pricing` page reuses Landing's pricing section, so it reads Landing's pricing slots now (issue 02 may give it its own). Header and footer words are still in code (issue 02's Shared tab). The browser tab title falls back to the root layout's "Zeph" only when Copy can't be read. Saved text has surrounding spaces trimmed.
  - Review notes left for later: switching tabs on the Copy page drops drafts (only one tab now; issue 02 adds the prompt). A slot key missing from Copy (seed and page out of step) would crash the render rather than show the error state; the Landing tests read every key from the seed, so drift fails the tests first.

### Evidence per criterion

1. Seeding: `tests/test_copy.py::test_reseeding_keeps_an_edited_text_and_follows_the_seed_for_the_rest` (edited text kept; name, max length, placeholders follow the seed; removed slot gone); prestart calls `seed_copy`; the running worktree stack served all seed slots after start.
2. Public read: `test_signed_out_visitors_read_every_slot_from_the_seed`; live `curl localhost:8010/api/copy` returned every key with no auth.
3. Admin read: `test_admin_sees_the_landing_tab_with_slots_in_page_order`; `CopyEditor.test.tsx` "shows the Landing tab's slots in page order…".
4. Tab save: `test_a_tab_save_applies_every_change…`, `test_each_bad_text_turns_away_the_whole_save…` (too long, missing placeholder, other tab), `test_empty_text_and_unknown_placeholders_are_turned_away`; `CopyEditor.test.tsx` shows each reason on its slot.
5. Plain User refused: `test_a_plain_user_cannot_read_the_copy_page_or_save` (403 both), plus the existing all-admin-routes-403 test.
6. Landing only Copy: `Landing.test.tsx` "shows only Copy text in every section…" (marked Copy, nothing else left once icons are set aside); `page.test.tsx` metadata from Copy; live page `<title>Zeph — Your AI companion</title>` and description from Copy.
7. Error state: `page.test.tsx` and `pricing/page.test.tsx` error-state tests; live: backend stopped → signed-out `/` showed "Couldn’t load this page" / "Check your connection, then try again." with Try again.
8. Checks: `ruff check` (All checks passed!), `ruff format --check` (504 files already formatted), `mypy` (no issues in 189 files), `pytest -n auto` (1329 passed); `pnpm lint` (clean), `pnpm format:check` (All matched files use Prettier code style!), `pnpm typecheck` (clean), `pnpm test` (118 files, 732 passed). Placeholder helper: `lib/copy.test.ts` (7 tests).
9. Pixel test (fixture mode, `BASE_URL=http://localhost:3110`): `PASS Landing 0.03% differs, height 4228 vs 4228`, `PASS M-Landing 0.04% differs, height 6099 vs 6099`; HowItWorks and M-HowItWorks also PASS. (The later review rename of `slot` → `slotPrefix` changes no markup.)
10. /run look: Copy page at 1280 and 390 against Persona (FormEditor), Check-in Kinds (CardSaveBar) and the Memories tab row: same editor box, caption, mono counter, tab underline; no new colours or sizes. Screenshots: `archive/01-screenshots/copy-1280.png`, `copy-390.png`, `persona-1280.png`, `kinds-1280.png`.
11. /run flow (worktree stack, signed-in Admin): changed "Main heading, first line" to "Think Slower,", saved ("Saved. It shows on the next page load."), a signed-out browser on `/` read h1 "Think Slower, Live More Deliberately." (`landing-changed.png`); a 41-character heading was turned away with "Keep it to 40 characters or fewer." on that slot (`copy-too-long.png`).

## Completion

- Completed: 2026-11-19
- Commit: merge `78af035` into main — "Merge Copy issue 01: Landing reads every word from Copy (store apart from Platform Settings, public read, Admin Copy page with all-or-nothing tab save); Landing and Pricing show the error state when Copy can't be read"
  - Branch `copy-01-landing`:
    - `478e804` Copy 01: Landing reads every word from Copy, with the Copy admin page
    - `5e450b3` Copy 01: name the Landing key prefixes slotPrefix (review)
    - `6f1802e` Copy 01: evidence recorded, issue completed and archived, screenshots at both widths; CONTEXT says what a Copy slot is
