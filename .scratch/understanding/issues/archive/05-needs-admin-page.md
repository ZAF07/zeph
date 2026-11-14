# 05 — Needs admin page

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Admins manage Needs on the Dashboard, like Check-in Kinds: add, edit (name, "when it fits", "how to reply"), reorder and delete. Names are unique ignoring case. The fallback Need can be edited but not deleted. Changes reach the next Understanding with no redeploy.

## Acceptance criteria

- [x] Admin API: list, create, update, delete Needs; deleting the fallback is refused; duplicate names (ignoring case) refused
- [x] Admin page following `docs/design/zeph-admin.html` where it fits; Vitest + RTL tests
- [x] An edited "how to reply" reaches the next reply's instructions (webhook-seam test)
- [x] A deleted Need is no longer offered to the Understanding; saved Understandings that named it are untouched
- [x] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm` checks pass
- [x] `/run-dashboard`: add, edit and delete a Need as an Admin; the fallback's delete is blocked

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`

## Comments

- Branch `understanding-05-needs-admin`, worktree `ai-chat-companion-understanding-05` (ports 3190/8190/5622).
- Plan: core `NeedService` (list, add, update, delete, move), like Check-in Kinds plus Helplines' move up/down. Need repository gains `get`, `add`, `update`, `delete`, `set_sort_orders`. Admin API under `/api/admin/needs`. Dashboard `/admin/needs`: a card per Need in order with Name, "When it fits", "How to reply", ↑/↓, Remove (with confirm) and Save; the fallback card says "Fallback · can't be deleted" and has no Remove.
- Decisions:
  - Length limits: name 80, "when it fits" 500, "how to reply" 2000 characters (seeded texts are at most 122 and 272). Spaces around each field are trimmed.
  - Deleting the fallback is a 409 (`FallbackNeedError`, like the international fallback Helpline). Its name and texts can be changed; it stays the fallback.
  - `MoveDirection` moved from `core/helplines.py` to `core/models.py`, since Helplines and Needs both use it.
  - The design file has no Needs screen, so the page follows the Check-in Kinds page, with cards in one column because order matters.
- Known edge cases, not fixed (platform not live, one Admin):
  - Names are unique ignoring case only in core. The `needs.name` database rule cares about case, so two Admins adding "advice" and "Advice" at the same moment could both succeed. A unique index on `lower(name)` would close it.
  - After a rename, this Conversation's earlier Understandings shown to the model still carry the old name. If the model copies it, the reply uses the fallback Need for that one Message.
  - Typing spaces around a name leaves Save enabled after saving, because the server trims. The Check-in Kinds card does the same.

## Evidence

- **Admin API (list, create, update, delete; fallback delete refused; duplicate names ignoring case refused):** `tests/test_admin_needs.py`: `test_admin_sees_the_needs_in_order_with_the_fallback_marked`, `test_admin_can_add_edit_and_delete_needs`, `test_bad_needs_are_refused` (blank, too long, "be HEARD" on add, "just chatting" on update → 422; a case-only rename of its own name is allowed; missing ID → 404), `test_the_fallback_need_can_be_edited_but_not_deleted` (409, then renamed and still the fallback), `test_admin_can_move_a_need_up_or_down`, `test_only_admins_can_manage_needs` (403). Error status codes are in `tests/test_core_error_status_codes.py`.
- **Admin page with Vitest + RTL tests:** `web/src/app/(dashboard)/admin/needs/page.tsx`, `web/src/components/NeedsManager.tsx`, `web/src/components/NeedCard.tsx`; "Needs" link in the admin sidebar. `web/src/components/NeedsManager.test.tsx` has 10 tests: order and fields, fallback marked with no Remove, save, add, backend refusal shown, remove after confirming, move up, no move past the ends, failed move, load error.
- **Edited "how to reply" reaches the next reply (webhook seam):** `test_an_edited_how_to_reply_reaches_the_next_reply`. The new text is in the reply call's instructions and the seeded text is not.
- **Deleted Need no longer offered; saved Understandings untouched:** `test_a_deleted_need_is_not_offered_and_saved_understandings_keep_its_name`. After the delete, the next Understanding call has no "- Advice:" line, and the earlier saved Understanding still says "Advice".
- **Checks (after the review fixes):** `make check`: `ruff check` all passed; `ruff format --check` 307 files already formatted; `mypy` no issues in 112 files; `pytest` 802 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean; `pnpm test` 51 files, 353 tests passed.
- **/run-dashboard** (worktree, signed in as an Admin, Playwright): `/admin/needs` listed the six seeded Needs in order. The "Ask more" card showed "Fallback · can't be deleted" and had 0 Remove buttons. Added "Celebrate" (it went last), edited its "how to reply" ("Saved Celebrate."), moved it up one place, and renaming "Advice" to "be heard" showed "There is already a Need called “be heard”." Removing "Celebrate" brought back the six. `DELETE /api/admin/needs/<fallback id>` from the signed-in browser returned 409 "The fallback Need can't be deleted, only edited." No page errors. The page also works at 390px wide. This was run again after the review fixes, with the same result. The database ended with the six seeded Needs.
- **/code-review:** Standards found no hard violations. Fixed: `MoveDirection` moved to models (its docstring said "Helpline"), plain length checks like the siblings, a named `Flash` type like `HelplinesManager`, and the card's unreachable 409 branch removed. Kept as they are: the move logic is like Helplines' and the card is like `CheckInKindCard`, which matches how the other admin pages are built. Spec found nothing missing. Its edge cases are listed above.

## Completion

- Completed: 2026-11-14
- Commits: `4153b62` (Needs admin page), `1fffc47` (review fixes)
