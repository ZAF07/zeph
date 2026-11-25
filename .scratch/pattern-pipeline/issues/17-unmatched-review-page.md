# 17 — Admins review what Zeph keeps noticing that fits no Pattern Type

Status: ready-for-agent
Track: B
Blocked by: 16

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 84, 85). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

An Admin page lists what keeps turning up unmatched, so the catalog can grow. To protect privacy each entry is a general description with no User details (no names, quotes, places or dates) and how many Users it appeared for. The description is written when the unmatched Pattern is kept, about the way of acting and never about the person, and like descriptions are grouped by meaning. The Admin marks each entry: new Pattern Type, folded into an existing one (naming it), or dropped. Writing the YAML stays manual. The model-suggestions feature is out of scope (parked in the decisions file).

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The page lists unmatched entries with a general description and a count of Users, most Users first
- [ ] No entry shows a User's name, quote, or any detail that could identify them; a test checks the description is built only from the general wording
- [ ] Like descriptions from different Users are grouped into one entry
- [ ] An Admin can mark an entry as new Pattern Type, folded into a named Pattern Type, or dropped, and filter by that
- [ ] A dropped entry doesn't return unless it appears for more Users
- [ ] A non-Admin can't reach the page or its API
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `16-existing-patterns-move-across-and-unmatched-patterns.md`

## Comments

Plan (25 Nov 2026, branch `pattern-17-unmatched-review-page`, worktree `ai-chat-companion-pattern-17`):

- **General description.** The Pattern keeping step writes a `general` line with each new unmatched Pattern: the way of acting only, no names, quotes, places or dates. For an unmatched Pattern kept earlier with none (the live User's), it is asked for one too. Code drops a description holding a digit, a quote mark or the User's name; the Pattern is still kept and is asked about again next time. Saved as `patterns.general_description`. The keeping prompt is reloaded from the seed.
- **Entries, grouped by meaning.** New table `unmatched_entries` (description, embedding, mark, Pattern Type folded into, Users when marked, when). No User ID on it. When a Pattern gets its general description, code embeds it and links the Pattern to the closest entry at or over a new Admin-set bar (`unmatched_grouping_closeness_percent`), or starts a new entry with that description. The entry's words are only ever a general description.
- **Count.** Users with an unmatched Pattern linked to the entry that the matching command hasn't linked to a Pattern Type. Entries with no Users left aren't listed.
- **Marks.** To review, new Pattern Type, folded (naming a Pattern Type in the catalog), dropped. Saved with the User count at that time. A dropped entry reads as "to review" again only when its count is above that number.
- **API.** `GET /api/admin/unmatched-patterns?mark=` (most Users first) and `PUT /api/admin/unmatched-patterns/{id}/mark`, Admins only.
- **Page.** `/admin/unmatched-patterns`, card-list template with the table template's filter pills: one card per entry (description, mark tag, Users), open to set the mark and the Pattern Type. New reference `AdminUnmatchedPatterns.html`, baseline, menu link.
- **Migration 0096.** Adds the column, table and link. No User data is removed.
