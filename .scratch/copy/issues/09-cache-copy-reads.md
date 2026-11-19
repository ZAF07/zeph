# 09 — Copy: cache Copy reads

Status: needs-triage

## Parent

`.scratch/copy/PRD.md`

## Before any solution: grill with docs

**When this is picked up, run `/grill-with-docs` first and settle the approach before writing code.** The options below are starting points for that session, not a decision. Record what is decided in an ADR (or an update to ADR-0019) and fill in the acceptance criteria from it. Do not move this to `ready-for-agent` until that is done.

## Why

Issue 01 reads Copy from the database on every public page load (one query per load; the page and its tab title share it within a request). Nothing is cached, so a saved change shows on the next load whichever backend process serves it. That is simple and correct, but every visitor's page load becomes a database read, and once every page reads Copy (issues 02–08) that is every page load on the website.

## What to build

Cut the database reads behind Copy while keeping the rule from the PRD: an Admin's saved change shows on the next page load, and visitors never see half-old, half-new text.

## Questions for the grill

- How many reads is too many? Measure the cost of the current read before choosing (the platform isn't live yet).
- Where should the cache sit:
  - in the backend process, refreshed on save (the PRD allowed this);
  - in the Dashboard's server (Next.js fetch caching with a tag cleared on save);
  - HTTP caching (`Cache-Control` / `ETag`) or a CDN in front of the public read.
- How does a save reach every process holding a cache? ADR-0018 says there is one backend process today, but the standing rule is to design for many concurrent Users with no single-process assumptions. Decide which wins here.
- Is "shows on the next page load" still the rule, or is a short delay (seconds) acceptable?
- ~~What happens on a cache miss when the database is down: stale Copy, or the normal error state?~~ Decided 2026-11-19: stale Copy. Each web server keeps the last Copy it read and shows it, whole, when a read fails; with none, the normal error state. Still no default text in the web app (ADR-0019, PRD story 32).

## Acceptance criteria

To be written after the grill. At least:

- [ ] A saved change still shows on the next page load (or within the delay the grill agrees).
- [ ] A tab save never shows half its changes.
- [ ] Repeated page loads don't each read the database, shown by a test or measurement.
- [ ] When a Copy read fails, pages show the last good Copy this web server read; with none, the normal error state.
- [ ] Admin pages, the Copy page included, open even when Copy can't be read (today `DashboardFrame` shows the couldn't-load page in place of every page, admin ones too).
- [ ] `/run`: as an Admin, change a Landing slot, reload signed-out `/` and see it.
- [ ] `/run`: with the Copy read failing, a page loaded before still shows its words, and `/admin/copy` opens.

## Blocked by

- All other Copy issues (02–08) completed. The owner will revisit this after them.

## Comments

- 2026-11-19 — From issue 05's review: when Copy can't be read, `DashboardFrame` shows the couldn't-load page for every Dashboard page, admin pages included, so a failing Copy read locks Admins out of the Copy page. Agreed with the owner: fix it here, with "keep the last good Copy" and admin pages not depending on Copy. Storing Copy as files beside the web code was considered and rejected (ADR-0019).
- 2026-11-19 — From issue 08: Copy issues 02–08 are all completed, so this one's "Blocked by" is clear. The Dashboard menu now also reads the short AI notice from Copy (`shared.dashboard.ai_notice`, in `SidebarAiNotice`), so when admin pages stop depending on Copy, the menu needs that slot too, or should show nothing when Copy can't be read.
