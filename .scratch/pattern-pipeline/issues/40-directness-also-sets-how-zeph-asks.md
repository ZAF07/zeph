# 40 — The directness setting also sets how Zeph asks

Status: ready-for-agent
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

## Open questions, answered by the owner (Zaf) on 26 Nov 2026

1. The waits for gentle and direct: **5 days and 2 days** (balanced stays 3).
2. The Thought Experiment Approach: **unchanged**. It comes after "would it differ"; for gentle, after the story follow-up.
3. Does directness also change the fewest replies between two Curiosities, and the tries before an Exploration rests? **Yes, both change.** (The suggested answer was no.) The backing-off rules themselves stay fixed: the spacing still doubles after brush-offs, and "drop it" still rests an Exploration at once.
4. A User changes the setting while a question waits: **the waiting one stays**; the new setting applies from the next try.

## What to build

- **Order of Approaches, by setting:**
  - gentle: story follow-up → Thought Experiment → "this week, notice…" ("would it differ" is never used);
  - balanced: story follow-up → "would it differ" → Thought Experiment → "notice" (today);
  - direct: "would it differ" → story follow-up → Thought Experiment → "notice".
  The rules per need stay: a missing Condition never gets a Thought Experiment, and the state going in gets only story follow-up and "notice", for every setting (Zeph never names a state first).
- **Three numbers, each per setting.** Balanced keeps today's key and value. Starting numbers for the last two were picked by the agent, for the owner to correct:

  | | Gentle | Balanced | Direct |
  |---|---|---|---|
  | Wait after a try with nothing (days) | 5 | 3 | 2 |
  | Tries with nothing before resting | 3 | 4 | 5 |
  | Fewest replies between Curiosities | 4 | 3 | 2 |

  Six new Platform Settings with hints, overridable in Eval Variants. The fewest replies between Curiosities covers every Curiosity, not only aimed ones.
- **A setting changed mid-way:** a waiting aimed Curiosity is left as written; the next one is written under the new setting.
- **Words:** the Account page's help text, the chat tool `change_directness` (description and what the model is told back) and `reply_settings_instructions` say the setting also changes how Zeph asks. A migration reloads the Copy slot and the prompt unless an Admin edited them. The reference files `Account.html` and `M-Account.html` get the new help text.
- **Not changed:** the Reply Plan's own line on directness (still about the Read), the ready gate, sharing, struggling, never two Conversations in a row.

## Acceptance criteria

- [ ] A gentle User's Exploration starts with a story follow-up and never uses "would it differ"; a balanced User's is as before; a direct User's starts with "would it differ"
- [ ] The Thought Experiment Approach keeps its place: after "would it differ", and for gentle after the story follow-up
- [ ] This holds for all three needs (unclear story, counter-test, missing Condition), and the state going in is never asked by "would it differ", whatever the setting
- [ ] The wait after a try with nothing is 5, 3 and 2 days for gentle, balanced and direct
- [ ] An Exploration rests after 3, 4 and 5 tries with nothing in a row for gentle, balanced and direct; "drop it" still rests it at once for everyone
- [ ] The fewest replies between two Curiosities is 4, 3 and 2 for gentle, balanced and direct, and still doubles while Zeph backs off
- [ ] A waiting aimed Curiosity stays as written when the User changes the setting; the next try follows the new setting
- [ ] The six new numbers are on Platform settings with hints and can be overridden in an Eval Variant
- [ ] The Account page's help text, the chat tool's description and the settings instructions say the setting also changes how Zeph asks; an Admin's edited text is kept by the migration
- [ ] Unchanged for every setting: never two Conversations in a row, nothing while struggling, the ready gate
- [ ] `docs/pattern-pipeline/README.md`, `lifecycle.md`, `docs/message-pipeline/README.md`, `CONTEXT.md` and decision 7 in `grill-decisions.md` say what is built
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` and the web checks pass, and it was checked in the running app (`/run`): a gentle, a balanced and a direct User with the same suspected Pattern get a different first Approach and a different wait, and the Account page shows the new words

## Comments
