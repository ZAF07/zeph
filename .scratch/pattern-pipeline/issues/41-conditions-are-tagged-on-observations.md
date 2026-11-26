# 41 — Conditions are tagged on Observations: audience, stakes, state going in

Status: ready-for-agent
Track: A
Blocked by: none

## Parent

Issue 23 (`23-situations-vary-on-more-than-people.md`) holds every decision with its reason: read D4, D7, D8, D14, D16 and D17 first. ADR-0031. Terms: **Condition** in `CONTEXT.md`. How tagging works today: `docs/pattern-pipeline/tagging.md`.

## What to build

An Observation gains three Conditions beside relationship, power, setting and stance. The tagging step fills them, code checks them, and they are stored. Nothing reads them yet (issues 42, 43 and 44 do).

- **Lists** (closed, in `core/models.py` beside the others):
  - audience: one-to-one, group, in front of others (people watching who aren't part of it).
  - stakes: low, high (high: something that matters to the User could be lost).
  - state going in: worn out, under pressure, low, steady (how the User was before it happened, not after).
- **Tagging prompt:** given the three lists with one line each on what they mean. A Condition is filled only when the User's story says it; otherwise it is left empty, never guessed. One value per Condition: when a story gives two, the one it leans on, or empty when the model can't tell. State is as of when the story happened, from the User's own words in this Conversation. The prompt's lists are built from the enums if issue 31 has done that; otherwise follow what is there.
- **Checks (`plan_observations`):** a Condition with a value outside its list drops the Observation, as for today's tags (counted under "Dropped by code"). Empty is valid.
- **No state after a crisis:** Observations from a Conversation with a Safeguard Event are kept with state empty, whatever the model answered.
- **Storage:** three nullable columns on `observations` (a migration; mention it in the PR). No data migration: nothing was kept before (D16).
- **Privacy:** nothing new on "Things you said that Zeph kept", nothing new for Admins. The Conditions go with their Observation.
- **Prompt reload:** the migration reloads `pattern_tagging_prompt` with `reload_prompt_unless_edited`.
- **Tagging Eval:** a case may state the Conditions it expects for an Observation, "must be empty" included; when stated they must match for the case to pass, and the Case Result shows expected and kept Conditions. About 10 new seed cases, drafted for the owner to correct: each new Condition said, so tagged (3); nothing said, so all empty (2); the User says how they felt after, so state stays empty (2); two people and a group, audience against relationship (1); two cases of high stakes said plainly (2; issue 42 turns them into "anyone would" cases).

Evals cost money: show the owner the estimate before any run, and run only the new cases.

## Acceptance criteria

- [ ] The three lists exist as closed lists, and an Observation holds one value or none for each
- [ ] The tagging prompt explains the three Conditions, says to leave one empty when the story doesn't say it, and says state is before the event, from the User's own words
- [ ] An Observation with a Condition outside its list is dropped and counted; one with empty Conditions is kept
- [ ] An Observation from a Conversation with a Safeguard Event is stored with state empty
- [ ] The Conditions are stored and read back with the Observation; deleting the Observation removes them
- [ ] "Things you said that Zeph kept" and the Admin pages show nothing new
- [ ] A migration that reloads the tagging prompt keeps an Admin's edit
- [ ] A Tagging Eval case can expect Conditions, including "must be empty", and fails when they don't match
- [ ] About 10 new Tagging cases are in the seed, and the new cases have run once, with the Eval Run ID, score and cost in Comments
- [ ] The owner was shown the estimate before the run
- [ ] `docs/pattern-pipeline/README.md` and `tagging.md` say what was built
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass, and a real Conversation end was checked in the running app (`/run`): a story that says an audience, stakes and a state is stored with them, and one that says none is stored with them empty

## For the owner afterwards (not acceptance criteria)

- Correct the drafted Tagging cases (`docs/pattern-evals/adding-tagging-cases.md`).

## Comments
