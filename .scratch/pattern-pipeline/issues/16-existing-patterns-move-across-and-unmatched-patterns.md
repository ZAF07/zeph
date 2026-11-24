# 16 — Existing Patterns move across, and free noticing becomes unmatched Patterns

Status: ready-for-agent
Track: B
Blocked by: 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 28, 57, 86). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Production has a real User with Patterns kept under the old rules. A migration keeps every one: confirmed stay confirmed and visible, suspected become unmatched (they were hidden anyway), closed stay closed. A one-off pass, run by an Admin command, matches each to a Pattern Type where one fits.

The Pattern keeping step changes job: it no longer starts, confirms or closes catalog Patterns (code does, from Observations). It only notes what recurs across two or more Life Threads and fits no Pattern Type, as an unmatched Pattern with its evidence. Unmatched Patterns are never ready or shared and stay hidden, but still come to mind and the Read may think with them, as today. When a Pattern Type is added, an Admin command tags stored unmatched evidence again against it.

## Acceptance criteria

- [ ] After the migration every existing Pattern and its evidence is still there; confirmed ones still show on the Dashboard exactly as before
- [ ] Existing suspected Patterns are unmatched and hidden; closed ones stay closed
- [ ] The matching pass links a Pattern to a Pattern Type only where it fits, and reports what it did
- [ ] The keeping step writes only unmatched Patterns; it can't change a catalog Pattern's state
- [ ] An unmatched Pattern still comes to mind and can shape the Read, and is never offered as a Pattern
- [ ] Tagging again against a new Pattern Type turns matching unmatched evidence into Observations, checked like any other
- [ ] The migration is tested against a database holding old-style Patterns
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `12-patterns-scored-and-moved-by-code.md`

## Comments

Plan (24 Nov 2026, branch `pattern-16-existing-patterns-move`, worktree `ai-chat-companion-pattern-16`):

- **Unmatched is a state of a written Pattern.** `PatternState` gains `unmatched`, used only by Patterns with no Pattern Type (the ones the keeping step writes). It is not one of the seven states code moves a catalog Pattern between.
- **Migration.** Every old suspected Pattern becomes unmatched; confirmed and closed are left as they are; no row or evidence is removed. `patterns` gains `matched_pattern_type_id`. `pattern_keeping_prompt` is reloaded from the seed.
- **Keeping step.** Starts only unmatched Patterns (two or more Threads, as before) and adds evidence only to unmatched ones. It no longer reads reactions, confirms or closes. It is shown the Pattern Types so it leaves those to tagging. It never sees a catalog Pattern.
- **In replies.** An unmatched Pattern still comes to mind and the Reply Plan may build its Read on it, but code drops any try to offer it: only a confirmed Pattern can be offered.
- **Matching (Admin command).** `python -m companion.pattern_matching_terminal` (`make match-patterns`, `TYPES=ID,ID` for only some Pattern Types). For each written Pattern not matched yet, one model call says which Pattern Type it fits, or none; code keeps the answer only when the ID is in the catalog. A match is a link (`matched_pattern_type_id`); the Pattern, its words, state and evidence stay as they are. Then the Conversations behind its evidence whose messages are still kept are tagged again against that Pattern Type with the normal checks, and the User's Patterns are scored again (cause `evidence_tagged_again`). Closed ones are linked but not tagged again. Only for Users for whom Pattern noticing works and who pressed "Got it". The same command with `TYPES=` is the "tag again when a Pattern Type is added" step. It prints counts and IDs, never a User's words.
- **Admins** see an "Unmatched Patterns" count per User.
