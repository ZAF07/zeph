# 29 — Admins can edit every reply prompt note on the Dashboard

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md` (came out of the grilling on `issues/23-companion-claims-it-searched-the-web.md`)

## Problem

ADR 0004 says how the Companion behaves is Admin-managed, not code. These reply prompt notes are seeded into platform settings, but Admins can't see or change them on the Dashboard, so changing one needs a re-seed:

- `reply_web_search_instructions`
- `reply_features_unavailable_note`
- `reply_settings_instructions`
- `reply_delete_data_instructions`
- `reply_data_deletion_cancelled_note`
- `reply_memory_intro`
- `reply_knowledge_intro`
- `web_result_source_reminder`
- `web_search_tool_description`
- `page_fetch_tool_description`

(`sticker_tool_description` and `reply_web_search_limit_note` are editable already.)

## Decisions (grilling, 2026-11-13)

1. **On the Response composition card, in groups that fold shut.** All extra notes on that card sit in named groups, closed by default. One Save button for the whole card, as today. This needs a frontend change.
2. **Every extra note on that card is in a group**, including the two already there. Groups are defined on the backend on the Response composition `CoreService`; the page just shows what it's given. Photo viewing and Memory retrieval cards keep their flat list (no groups).

   | Group | Notes |
   |---|---|
   | Web search | `web_search_tool_description`, `page_fetch_tool_description`, `reply_web_search_instructions`, `reply_web_search_limit_note`, `web_result_source_reminder` |
   | Settings in chat | `reply_settings_instructions`, `reply_delete_data_instructions`, `reply_data_deletion_cancelled_note` |
   | Memory and Knowledge | `reply_memory_intro`, `reply_knowledge_intro` |
   | Features | `reply_features_unavailable_note` |
   | Stickers | `sticker_tool_description` |

3. **A setting can require several placeholders.** `required_placeholder` becomes a list for every setting (Crisis Reply and "Finish onboarding first" reply get a list of one). `reply_features_unavailable_note` requires both `{features}` and `{dashboard_url}`. The error names the missing one, e.g. "The Features unavailable note must include {dashboard_url}, the link to the Dashboard."
4. **The card shows the backend's reason when a save is refused** (422 with a detail), like `CheckInKindCard` does; any other failure keeps today's message. Groups are not opened automatically.
5. **Each note can carry a one-line hint** under its label saying when it's used, defined on the backend next to the label (taken from the seed file comments). Obvious ones (tool descriptions) leave it out.

Defaults picked (not grilled; change freely): labels and hints follow the seed file comments; tool descriptions and instructions get `max_length=4_000`, intros and notes `2_000`.

## Out of scope

Fixed replies sent to Users (welcome message, reply failed, etc.) and number/list settings. Those need their own Dashboard design.

## Acceptance criteria

- [ ] Each note above shows on the Response composition card, in its group, and saves
- [ ] Groups are folded shut by default and open on click
- [ ] Hints show under the labels that have one
- [ ] A saved note is used in the next reply
- [ ] The Features unavailable note can't be saved without `{features}` or without `{dashboard_url}`, and the card shows the reason
- [ ] Crisis Reply and "Finish onboarding first" reply placeholder checks still work
- [ ] Tests cover it
- [ ] Checked in the running app
- [ ] `make check` passes
