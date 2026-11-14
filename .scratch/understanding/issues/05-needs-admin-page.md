# 05 — Needs admin page

Status: in-progress

## Parent

`.scratch/understanding/PRD.md`

## What to build

Admins manage Needs on the Dashboard, like Check-in Kinds: add, edit (name, "when it fits", "how to reply"), reorder and delete. Names are unique ignoring case. The fallback Need can be edited but not deleted. Changes reach the next Understanding with no redeploy.

## Acceptance criteria

- [ ] Admin API: list, create, update, delete Needs; deleting the fallback is refused; duplicate names (ignoring case) refused
- [ ] Admin page following `docs/design/zeph-admin.html` where it fits; Vitest + RTL tests
- [ ] An edited "how to reply" reaches the next reply's instructions (webhook-seam test)
- [ ] A deleted Need is no longer offered to the Understanding; saved Understandings that named it are untouched
- [ ] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm` checks pass
- [ ] `/run-dashboard`: add, edit and delete a Need as an Admin; the fallback's delete is blocked

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`
