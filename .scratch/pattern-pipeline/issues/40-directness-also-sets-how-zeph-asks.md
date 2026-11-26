# 40 — The directness setting also sets how Zeph asks

Status: needs-info
Track: A
Blocked by: 43 (it renames "way" to Approach and changes the same code)

## Parent

`.scratch/pattern-pipeline/PRD.md`. Design: `docs/pattern-pipeline/README.md`. Decided by the owner (Zaf) on 25 Nov 2026 in the grill for issue 23 (its decision D15). It changes decision 7 in `.scratch/pattern-pipeline/grill-decisions.md`, which said the setting is only about the Read.

## Does it need a grilling session?

Not a full one. The shape is decided (below). Four small questions are left, each with a suggested answer. Confirm them with the owner before planning, then set this to `ready-for-agent`.

## The problem

A User sets how direct Zeph is: gentle, balanced or direct. Today that only changes how soon and how plainly Zeph says its Read. The Agenda never reads it, so a "direct" User and a "gentle" User get the same questions in the same order. A User who picks "direct" expects it to cover how Zeph asks too, and a "gentle" User deserves more room.

## What was decided

Directness changes where an Exploration starts and how long it waits. Nothing else.

| | Gentle | Balanced (today) | Direct |
|---|---|---|---|
| First Approach | story follow-up | story follow-up | "would it have gone differently if…" |
| "Would it differ" Approach | skipped: follow-up, then "notice" | used second | used first |
| Wait after a try with nothing | longer | 3 days (`exploration_wait_days`) | shorter |

Fixed for everyone, whatever the setting:

- Backing off after brush-offs; "drop it" is final.
- Nothing while they are struggling.
- Zeph never names a state first (issue 23, D12).
- Never two Conversations in a row on the same Exploration.
- The ready gate: directness never changes whether a Pattern may be shared.

Also decided:

- It applies to every Exploration need (unclear story, counter-test, missing Condition), not only Conditions.
- The Dashboard's words for the setting must also say it affects how Zeph asks, so Users know what they are choosing. The chat settings tool's description too.
- The waits are Admin-set numbers with hints, overridable in Eval Variants.

## Why

- Owner: the setting should also affect how pushy Zeph is.
- "Direct" must not become a licence to interrogate, so only the start and the wait move; every backing-off rule stays fixed.
- Turned down: keeping the same order for everyone and letting only the wording follow directness. It leaves a gentle User with the same questions as a direct one.

## Open questions (small, with suggested answers)

1. The waits for gentle and direct. Suggested: 5 days and 2 days.
2. Where does the Thought Experiment Approach sit for each setting? Suggested: unchanged, after "would it differ" (for gentle, after the story follow-up).
3. Does directness also change the fewest replies between two Curiosities, or tries before an Exploration rests? Suggested: no. Those protect every User the same.
4. A User changes the setting while a question waits to be asked. Suggested: the waiting one stays; the new setting applies from the next try.

## Acceptance criteria

To be written once the open questions are confirmed.

## Comments
