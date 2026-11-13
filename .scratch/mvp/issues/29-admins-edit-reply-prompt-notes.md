# 29 — Admins can edit every reply prompt note on the Dashboard

Status: needs-triage

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
- `sticker_tool_description`

(Issue 23 makes its new Web Search Limit note editable already.)

## Likely approach (not decided)

Add each to `EDITABLE_SETTINGS` and to the Response composition card's `extra_prompt_keys` in `src/companion/core/platform_settings.py`. The Prompts & models page already shows extra prompts on a card, so no frontend change should be needed. Check placeholders (e.g. `{features}`, `{dashboard_url}`) are protected the way the Crisis Reply's is.

## Out of scope

Fixed replies sent to Users (welcome message, reply failed, etc.) and number/list settings. Those need their own Dashboard design.

## Acceptance criteria

- [ ] Each note above shows on the Response composition card and saves
- [ ] A saved note is used in the next reply
- [ ] A note with a placeholder can't be saved without it
- [ ] Tests cover it
- [ ] Checked in the running app
- [ ] `make check` passes
