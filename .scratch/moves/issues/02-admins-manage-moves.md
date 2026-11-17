# 02 — Admins manage Moves, and Research needs Web Search

Status: ready-for-agent
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (migrations, the seed settings file, the Understanding module, the admin Dashboard). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins manage Moves on the Dashboard, and a Move can need a Feature.

- Admin API: list, create, edit, delete and reorder Moves; duplicate names (ignoring case) refused as a conflict; an unknown Move id is not found (ADR-0011). Deleting a Move removes it from every Need's rule-outs; Understandings and Move Outcomes that named it keep the name.
- Need create and edit accept ruled-out Moves.
- A Move may need a Feature. Research needs Web Search (seed and migration). A Move whose Feature doesn't work for the User, or whose daily limit is used up (the Web Search Limit), is never offered to the Understanding. The reply then follows the existing Web Search wording: it says plainly it can't look things up (on their account, or until tomorrow), answers from what it knows, and never claims it searched.
- Dashboard (TanStack Query, ADR-0012; one API client): an admin Moves page modelled on the Needs page (no design in `docs/design/`, copy the Needs page's look) with add, edit, delete, reorder and the needed Feature; the Need edit form gains a ruled-out Moves picker.
- Changes reach the next reply.

## Acceptance criteria

- [ ] Admins add, edit, delete and reorder Moves through the API and Dashboard; duplicate names are refused.
- [ ] Deleting a Move clears it from Needs' rule-outs.
- [ ] Need rule-outs are saved and change which Moves the Understanding is shown.
- [ ] With Web Search off for a User, or its limit used up, Research is never offered, and the reply says so plainly without claiming it searched.
- [ ] API tests (prior art: the Admin Needs tests), webhook tests for gating, Vitest + RTL tests for the pages; backend and web checks pass.
- [ ] `/run`: Admin edits a Move on the Dashboard and the next reply uses it; with Web Search off for the owner, Research isn't picked.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`
