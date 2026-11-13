# 29 — Admins can edit every reply prompt note on the Dashboard

Status: completed

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

- [x] Each note above shows on the Response composition card, in its group, and saves
- [x] Groups are folded shut by default and open on click
- [x] Hints show under the labels that have one
- [x] A saved note is used in the next reply
- [x] The Features unavailable note can't be saved without `{features}` or without `{dashboard_url}`, and the card shows the reason
- [x] Crisis Reply and "Finish onboarding first" reply placeholder checks still work
- [x] Tests cover it
- [x] Checked in the running app
- [x] `make check` passes

## Comments

Evidence (2026-11-13):

- **Notes show in their groups and save:** `test_response_composition_shows_every_reply_note_in_its_group` and `test_every_reply_note_is_editable_with_its_seeded_value` (`tests/test_admin_settings.py`). In the running app (worktree stack, signed in as an Admin) the card showed the groups Web search, Settings in chat, Memory and Knowledge, Features and Stickers; a changed Web search instructions note saved, showed "Last saved … by Run check" and stayed after a reload.
- **Folded shut by default, open on click:** in the running app, no group was open on load; clicking Features opened only that group. Frontend test "folds each group shut until it is clicked".
- **Hints:** in the running app, the Features unavailable note showed its hint under the label. Frontend test "shows a hint under the labels that have one"; backend test `test_reply_notes_carry_a_hint_saying_when_they_are_used`.
- **A saved note is used in the next reply:** `test_saved_reply_notes_are_used_in_the_next_reply` (web search instructions, both web tool descriptions and Settings in Chat instructions reach the reply call). In the running backend, `WebSearchTools.offer` for the signed-in Admin returned the instructions saved from the Dashboard.
- **Features unavailable note needs both placeholders:** `test_the_features_unavailable_note_must_keep_both_placeholders` (each missing one, with its message). In the running app, saving "Not available: {features}." showed "The Features unavailable note must include {dashboard_url}, the link to the Dashboard." on the card. Frontend test "says why when the backend refuses a save".
- **Crisis Reply and "Finish onboarding first" checks still work:** existing tests in `tests/test_admin_safety.py` and `test_the_onboarding_unfinished_reply_must_keep_the_dashboard_link` pass on the new placeholder list.
- **`make check`:** passed after the review fix and rebase on main: 593 Python tests passed, ruff/format/mypy clean; web lint, format, typecheck clean and 319 tests passed.
- **Review:** standards and spec reviews found no hard violations or spec gaps. Fixed: the Features note now uses the shared `DASHBOARD_URL_PLACEHOLDER` constant. Left as is: the repeated 422-detail check (already in five forms before this change), and the flat list kept for other services (by design, Decision 2). No `CONTEXT.md` or ADR change: groups, hints and the placeholder list are Dashboard presentation, not new domain terms.

## Completion

- Completed: 2026-11-13
- Commit: 93d274a (merge into main): "Merge MVP issue 29: Admins can edit every reply prompt note on the Dashboard; …"
  - c21964c "MVP issue 29: Admins can edit every reply prompt note on the Dashboard"
  - 305d1c3 "MVP issue 29: use the shared Dashboard link placeholder in the Features unavailable note"
  - 80d214b "MVP issue 29 done: archive issue with test, run and review evidence"
