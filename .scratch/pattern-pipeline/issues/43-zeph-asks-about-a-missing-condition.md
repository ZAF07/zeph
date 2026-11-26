# 43 — Zeph asks about a missing Condition, and "way" becomes Approach

Status: ready-for-agent
Track: A
Blocked by: 41

## Parent

Issue 23, decisions D5, D6, D12, D13 and D15 (last paragraph). ADR-0031. Terms: **Condition**, **Approach**, **Exploration** in `CONTEXT.md`. Today's rules: `core/agenda.py` (`open_needs`, `next_way`, `aimed_question`) and "Explorations and the Agenda" in `docs/pattern-pipeline/README.md`.

## What to build

Code keeps count, for each suspected Pattern, of which Condition values it has seen and which it hasn't, and aims one question at an unseen value when the stories so far are one-sided. Zeph asks no more often than today.

- **Coverage table** (pure, worked out from the Pattern's Observations, never stored): for each Condition (relationship, power, stance, setting, audience, stakes, state) and each value, the number of clear stories for and clear stories against. Clear means not unclear, not situational, not excluded.
- **A "missing Condition" need** replaces "missing part of life". A Condition's value is an open need only when all hold:
  1. at least `condition_one_sided_stories` (2) clear stories for the Pattern have that Condition known and all share one value;
  2. another value of it has no clear story, for or against (that value is what to learn);
  3. only the most one-sided Condition is a need (the most stories behind it; ties go by a fixed order of Conditions);
  4. a useful try closes that value for good; tries with nothing rest the Exploration as today.
- **Order of needs:** unclear story, then counter-test, then missing Condition (the counter-test moves ahead of where "missing part of life" was).
- **Approaches for this need,** least pushy first: story follow-up → "would it have gone differently if…" (any Condition: "…if it had been just the two of you", "…if less was riding on it") → "this week, notice whether it's the same when…". No Thought Experiment for this need.
- **State is never named first:** for a state gap the instruction asks openly ("how were you doing going into that?"), only as a story follow-up or a "notice", and never offers a state.
- **The instruction** is written by code with the Condition and the value to learn, never the Pattern's name or the User's quote, as today; the model words it or leaves it when the moment is wrong. The Reply Plan and the Reply see the need in plain words, like today's needs.
- **Outcome and evidence:** as today. An answer to "would it differ" is a "what if" answer.
- **Rename:** `ExplorationWay` and the stored column on `exploration_tries` become Approach (a migration; mention it in the PR). Prompts, hints, the Agenda's text for the Reply Plan, Eval field `aimed_way` and docs follow. A prompt reload uses `reload_prompt_unless_edited`.
- **Number:** `condition_one_sided_stories` is a Platform Setting with a hint in the Patterns section, overridable in Eval Variants.
- **Directness** is not read here: the order is the same for every User (issue 40 changes that).
- **Understanding Eval:** 3 new Agenda cases, drafted for the owner to correct: a one-sided Pattern gets a question aimed at the unseen value; a Pattern that isn't one-sided gets none; a state gap is asked openly with no state named (a Judge rule).

Evals cost money: show the owner the estimate before any run, and run only the new cases.

## Acceptance criteria

- [ ] The coverage table counts clear stories for and against per Condition value, and leaves out unclear, situational and excluded ones
- [ ] A missing-Condition need opens only when rules 1 to 3 hold, with tests for: one story only, two stories with different values, the other value already seen against, two Conditions both one-sided
- [ ] Home, work and social are handled by this rule; the old "missing part of life" need and its code are gone
- [ ] The order of needs is unclear story, counter-test, missing Condition
- [ ] A useful try closes that value and it is not asked again; a try with nothing leads to the next Approach after the wait, as today
- [ ] The three Approaches are used in order for this need, and a Thought Experiment never is
- [ ] For a state gap the instruction names no state and is never a "would it differ"
- [ ] The instruction never holds the Pattern's name or the User's quote
- [ ] The existing limits still hold with this need: never two Conversations in a row, the wait after nothing, resting, nothing while struggling
- [ ] "Way" is renamed Approach in code, the stored column, prompts, hints, Evals and docs; existing tries keep their value through the migration
- [ ] `condition_one_sided_stories` is on Platform settings with a hint and can be overridden in an Eval Variant
- [ ] 3 new Agenda cases are in the seed and have run once, with the Eval Run ID, result and cost in Comments; the owner was shown the estimate first
- [ ] `docs/pattern-pipeline/README.md`, `lifecycle.md` and the `CONTEXT.md` notes on Condition, Approach and Exploration say what is built
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass, and it was checked in the running app (`/run`): a User with a suspected Pattern seen only in a group gets, in a later Conversation, a question about one-to-one, and the trace page shows the need and the Approach

## For the owner afterwards (not acceptance criteria)

- Correct the 3 drafted Agenda cases.

## Comments
