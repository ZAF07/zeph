# PRD: To-build features — making every "To build" part of the redesign real

Status: needs-triage

Blocked by: `.scratch/redesign/PRD.md` (all slices merged)

> Stub. Grill this (`/grill-with-docs`) before splitting it into issues.

## Problem Statement

The redesign (PRD `redesign`) builds every page exactly as drawn in `web/design/`. Parts with no backend yet are shown on sample data, with an orange "To build" tag. Users and Admins see these parts but can't use them, and the admin menu's "Plans" item opens only a "To build" empty state.

## Solution

Make each "To build" part real, one at a time, and remove its tag. Each one keeps exactly the look already drawn in `web/design/`.

## Scope (to confirm in grilling)

Every orange "To build" tag in `web/design/reference/`. Known so far:

- **Admin Plans** (admin menu, under Evals). It has no reference file, so it needs a design from Claude Design first.
- **Plan** page (`/plan`) for Users, plus billing behind it.
- **Admin Overview** (`/admin`): real counts (Users, Messages today, Check-ins today, Safeguard Events), the **Paying subscribers** tile with its breakdown by plan, the "Needs attention" list and the Features summary.
- Other "To build" tags on Home, Memories, Check-ins, Account, Connect Telegram and Users. Grilling lists each one from the reference files.

## Rules carried over

- `web/design/` is the design. Read `web/design/README.md` in full first. Its one rule, its "stop and ask" list and its pixel test all apply here (ADR 0018).
- A new page or part needs its reference file and baseline added to `web/design/` (by Zaf, through Claude Design, then `shoot.cjs`) before it's built, and must pass `compare.cjs` at both widths.
- Design-fixture mode stays the way the test gets its data. New data shapes get fixture values copied from their reference file.
- Decisions behind the redesign are in `.scratch/redesign/PRD.md` and its issues.

## Open questions for grilling

- Billing: provider, plans and prices, who pays, and what a plan unlocks (needs a port and an adapter, ADR 0003).
- What Admin Plans shows and lets an Admin change.
- Where each Overview count comes from, and how often it refreshes.
- Which tags are worth building now and which wait.
