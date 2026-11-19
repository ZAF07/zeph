# PRD: Copy — Admins edit the website's words from one page

Status: ready-for-agent

Blocked by: all of `.scratch/redesign/` being completed (issues 14 and 15 were in flight when this was written).

## Problem Statement

Admins can already change how Zeph behaves from the Dashboard: the Persona, prompts, models, chat wording and limits are all Platform Settings (ADR-0004). But most of the words on the website are written into the web app's code. That covers the Landing, Pricing and How it works pages, onboarding, and the User's side of the Dashboard (headings, buttons, empty states, error messages, page titles). Changing a heading or fixing a typo needs a developer and a deploy.

The few website words that Admins can edit today (the AI notice, the Memory notes, the Photo Viewing explanation, the Delete My Data description) sit on the Settings page among numbers and limits. Some of them carry `**bold**` markup inside the text.

## Solution

A new **Copy** admin page (`/admin/copy`) holds every word Users and visitors read on the website, all on one page, with one tab per website page. Admins change the words; the design decides how they look and where they sit. A saved change shows on the next page load, with no deploy.

Copy is made of fixed slots that the code defines (e.g. "Landing: main heading"). Each slot holds plain text, may take named placeholders such as `{count}`, and has a max length. Defaults come from a seed file, the same way Platform Settings do.

What the Companion says in chat, and anything the Companion is told, stays in Platform Settings on its current page. The Crisis Reply stays on Safety. See ADR-0019 and **Copy** in `CONTEXT.md`.

## User Stories

1. As an Admin, I want one Copy page in the admin area, so that I know where to change any word on the website.
2. As an Admin, I want the Copy page split into one tab per website page (Landing, Pricing, How it works, Onboarding, Home, Memories, Check-ins, Connect Telegram, Account, and a Shared tab for the parts every page has, such as the menu and footer), so that each view is short.
3. As an Admin, I want each tab's slots listed in the order they appear on the page, so that I can find a piece of text by where I saw it.
4. As an Admin, I want each slot to have a short, clear name (e.g. "Main heading", "Sign-up button"), so that I know which text I'm changing.
5. As an Admin, I want to search all tabs by the text a slot holds now, so that I can find "that sentence" without knowing its tab.
6. As an Admin, I want a search result to take me to the slot's tab with the slot in view, so that I can edit it straight away.
7. As an Admin, I want to edit several slots in a tab and save them together, so that a section I rewrite goes live as one change.
8. As an Admin, I want a tab's save to apply all its edits or none, so that visitors never see half-new, half-old text.
9. As an Admin, I want to be asked before I switch tabs or leave the page with unsaved edits, so that I don't lose work.
10. As an Admin, I want a slot to show which placeholders it takes (e.g. `{count}`), so that I keep live values in my sentence.
11. As an Admin, I want a save turned away if I left out a placeholder a slot needs, with the reason shown on that slot, so that the page never shows a sentence missing its value.
12. As an Admin, I want a save turned away if I typed a placeholder the slot doesn't know, with the reason shown on that slot, so that visitors never see `{nmae}` on the page.
13. As an Admin, I want to move placeholders anywhere in the sentence, so that I can word it naturally.
14. As an Admin, I want text that changes with a number to have a "one" slot and a "many" slot, so that "1 Memory Item" and "3 Memory Items" both read right.
15. As an Admin, I want each slot to show a character counter against its max length, so that I know how much room the design has.
16. As an Admin, I want a save over a slot's max length turned away, with the reason shown on that slot, so that a long heading can't break the page on a phone.
17. As an Admin, I want an empty slot turned away on save, so that no heading or button goes blank.
18. As an Admin, I want each slot to hold plain text only, so that I can't break the design's styling by accident.
19. As an Admin, I want text that the design shows as a notice's title (e.g. "Memory is paused.") to be its own slot, so that I can change it and the design still shows it as the title.
20. As an Admin, I want my saved change to show on the next page load, so that I can check it right away.
21. As an Admin, I want to see who last changed a slot and when, so that I know where a wording came from.
22. As an Admin, I want each website page's browser tab title and search description to be Copy, so that I can tune how Zeph shows in search results and link previews.
23. As an Admin, I want empty states, loading messages and the website's own error messages on User pages to be Copy, so that Users hear one voice even when something goes wrong.
24. As an Admin, I want the AI notice, the short AI notice, the User Memory explanation, the Photo Viewing explanation, the "Memory is paused" and "Memory isn't available" notes and the Delete My Data description on the Copy page, so that all website words are in one place.
25. As an Admin, I want those notes off the Settings page once they move, so that each piece of wording has exactly one home.
26. As an Admin, I want the onboarding "What brings you here?" choices to stay on Settings, so that a list the Companion is told about stays with the other things that shape it.
27. As an Admin, I want the chat wording (welcome message, reply failed, Limit Reply and the rest) to stay where it is, so that what the Companion says stays with the Persona and Evals.
28. As an Admin, I want the Crisis Reply to stay on Safety next to the Helplines, so that it is reviewed together with them and never changed casually next to button labels.
29. As a plain User, I don't want to see the Copy page or call its save, so that only Admins change the website's words.
30. As a visitor, I want the Landing, Pricing and How it works pages to show the current Copy without signing in, so that I read what Zeph says today.
31. As a User, I want onboarding and my Dashboard pages to show the current Copy with my own values filled in, so that the words read naturally.
32. As a visitor, I want the website to keep showing the last Copy it read when it can't reach the backend, and its normal error state only when it has none, so that a backend blip doesn't take the website down and I never see half-filled text.
33. As a developer, I want each slot's default text, name, tab, max length and placeholders kept in one seed file, so that adding a slot means one seed entry plus the page code that shows it.
34. As a developer, I want new slots in the seed added on startup and slots an Admin already edited left alone, so that a deploy never overwrites an Admin's wording.
35. As a developer, I want the seed text to match the design references, so that the pixel test keeps proving every page matches the design.
36. As a developer, I want the page code to name slots by key and never hold default text, so that there is one source of truth for the words (ADR-0004).

## Implementation Decisions

- **Copy is its own store**, kept apart from Platform Settings (ADR-0019), seeded from its own seed file next to the Platform Settings seed. It is seeded in prestart alongside the other seeds: slots not stored yet are added, and stored slots keep their text. A slot's name, tab, order, max length and placeholders always come from the seed; only its text is the Admin's. Slots removed from the seed are removed from the store.
- **A slot** has: a stable key (e.g. `landing.hero.heading`), the tab it belongs to, its order in that tab, a short name, its text, a max length, the placeholders it requires (by name), who last changed it and when.
- **Core module**: a Copy service, behind a Copy repository port, with: read all Copy (for the website), read the Copy page (slots grouped by tab, for Admins), and save one tab's changed texts. The save checks each text for: not empty, within max length, every required placeholder present, no unknown placeholder. Any failure turns away the whole save, with a reason per failing slot. A save can change only slots in the named tab.
- **Placeholders** are written `{name}`. Plurals are two slots ("one" and "many"); the web app picks one by the number. There are no plural rules or formatting inside the text.
- **Plain text only.** No markdown, links or HTML are read from Copy. Links, buttons and styling stay in page code; Copy gives only their words. A notice title in the design is its own slot.
- **HTTP API**:
  - A public read of all Copy (no sign-in), returning every slot's key and text. The backend may keep this in memory and refresh it on save, so a change shows on the next page load.
  - An Admin read of the Copy page: tabs in order, each with its slots (key, name, text, max length, placeholders, last changed by and when).
  - An Admin save of one tab: the changed slots' keys and texts. A bad save is turned away with field errors keyed by slot, the same way the settings pages are.
  - Admin endpoints follow the existing Admin check. A plain User is refused.
- **Moved out of Platform Settings**: AI notice, short AI notice, User Memory explanation, Photo Viewing explanation, "Memory is paused" note, "Memory isn't available" note and Delete My Data description become Copy slots. The two Memory notes each split into a bold lead slot and a body slot. The Settings page drops these fields. Endpoints that sent this wording inside other data (e.g. the Home data and the signed-in User's Memory note) stop sending it; the web app picks the right slot from the flags it already gets. The platform isn't live, so a migration only needs to drop the old settings; no backfill (seed text is the starting text).
- **Stays in Platform Settings**: the onboarding reason choices (the Companion is told them), all chat wording, and the Crisis Reply (on Safety).
- **Not Copy**: admin pages' own words; text the backend sends from its own rules (validation reasons); the text inside Clerk's sign-in and sign-up forms (set in Clerk). Our words around those forms are Copy.
- **Dashboard**:
  - The API client gets the Copy reads and the save. Pages never fetch it directly.
  - Website pages (Server Components where they are now) read Copy through the API client, and fill placeholders with one small pure helper. Page titles and descriptions come from Copy through the App Router's metadata.
  - Client components get Copy through a TanStack Query hook (ADR-0012), not prop-drilled from the root.
  - If Copy can't be read, the page shows the last Copy this web server read, whole; only if it has none does it show the website's normal error state. No default text is bundled into the web app. Admin pages never depend on Copy: they open even when it can't be read, so the Copy page is always reachable (issue 09).
  - The Copy admin page is one page with tabs. It has no reference file, so it is built only from the design's existing parts and token values (`web/design/README.md`, "Building new UI"): tabs like `MemoriesTabs`, a `FormEditor`-style text field per slot with a counter, the `CardSaveBar`, the existing unsaved-changes warning, `SearchField` and `EmptyState`. No pixel test covers it; it is checked by eye at 1280 and 390. Search filters slots across tabs by current text and jumps to the slot.
  - The design fixture API client used by the pixel test serves the seed Copy.
- **Rollout order**: Landing end to end first (seed slots, store, public read, Copy page with one tab, checks, Landing reading Copy). Then the other pages, one at a time. The wording moved out of Platform Settings comes last.

## Testing Decisions

- Good tests check what an Admin, User or visitor can see and do through the seam, not how the store or components are built inside. No tests on private helpers or table shapes.
- **Backend seam: the HTTP API** through the test client against the test database (prior art: `tests/test_admin_settings.py`, `tests/test_admin_safety.py`). Covers:
  - startup seed: new slots appear with seed text; an edited slot keeps its text after a re-seed; slot names, max lengths and placeholders follow the seed;
  - public read works signed out and returns the latest saved text;
  - Admin read groups slots by tab in order, with last-changed details;
  - tab save: applies all changes; turns away the whole save over max length, empty text, missing placeholder or unknown placeholder, with errors keyed by slot; turns away a slot from another tab; refuses a plain User;
  - moved wording: no longer in Platform Settings reads or saves, and served as Copy.
- **Dashboard seam: pages and components with a fake API client** (Vitest + React Testing Library; prior art: the existing settings page and Memories tests, `render-with-queries`). Covers:
  - each converted page shows the Copy it's given, with placeholders filled and the right one/many slot picked;
  - a page shows the last good Copy when a read fails, and the error state when there is none;
  - the Copy page: tabs and slot order, search jumps to a slot, counter, one save per tab, field errors shown on the right slot, the unsaved-changes prompt when switching tabs.
- The placeholder-filling helper gets small pure tests (prior art: `lib/*.test.ts`).
- **Pixel test** (ADR-0018) keeps running unchanged against the design references, with the fixture client serving seed Copy.
- `/run` checks in the running app: edit a Landing slot as an Admin, reload the signed-out Landing and see it; try a bad placeholder and see it turned away.

## Out of Scope

- More than one language, and choosing a language per visitor.
- Rich text, markdown or links in Copy.
- Admins adding, removing or moving slots or sections (page structure).
- Editing text in place on the live website.
- Copy history, undo and "reset to default".
- The admin pages' own words.
- Backend validation reasons, chat wording, the Crisis Reply, and the onboarding reason choices.
- Clerk's own form text.
- A fallback copy of the text inside the web app for when the backend is down, meaning default text written into the code. A copy kept in memory from an earlier read is allowed (issue 09).

## Further Notes

- Decisions came from a `/grill-with-docs` session on 2026-11-19. See ADR-0019 and the **Copy** entry in `CONTEXT.md`.
- ADR numbering: there are already two `0018` ADRs. Check that 0019 is still free when this lands.
- Copy touches every User page component, so it must start only after all redesign work is merged.
- Issue 03 (onboarding): onboarding reads Copy on the server and passes its own slots to the client flow (`pickCopy`), rather than a TanStack Query hook, so web code holds no "loading Copy" words. The page needs Copy on the server anyway for its title and error state.
