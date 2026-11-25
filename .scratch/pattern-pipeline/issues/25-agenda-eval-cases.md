# 25 — Eval cases for the Agenda: is the aimed question asked well, and is the answer read right

Status: ready-for-agent
Track: B
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (the Agenda and Explorations, the Evals section). Design: `docs/pattern-pipeline/README.md` ("Explorations and the Agenda", "Thought Experiments", "Tagging and Checks"). What each Eval can and can't show: `docs/pattern-evals/README.md`. Raised by the owner on 25 Nov 2026, after issue 19: the Whole-pipeline Eval's scripted User never answers Zeph, so the Agenda runs there but is not tested (issue 20, section 19, "The scripted User never answers Zeph").

## Why

The Agenda's rules are code and have ordinary tests (`tests/test_agenda.py`, `tests/test_explorations.py`, `tests/test_thought_experiments.py`). Three things only a real model can show have no Eval at all:

1. Whether the Reply Plan picks the aimed Curiosity at a fitting moment, and leaves it when it shouldn't ask.
2. Whether the reply asks it well, and never names the Pattern or quotes the User back.
3. Whether the tagging step reads the User's answer right: an unclear story settled, or not.

## What to build

No new Eval kind (owner's decision). Two existing kinds each learn one thing, and about 10 new cases are seeded.

**A. The Understanding Eval gets a made-up Agenda.** A case's made-up User Memory can hold suspected Patterns: the Pattern Type, its Observations (quote, sign, for or against, unclear with its second Pattern Type, who it is about, Life Thread, part of life, days ago) and the tries already made at it (need, way, outcome, days ago). The made-up User has Pattern noticing (told) and Pattern exploring on. Setup saves these as the real rows and then lets the real code build the Agenda, so the aimed Curiosity is the one `AgendaKeeper` writes, not one typed into the case. A case may also give the Thought Experiments on the platform.

New things a Message can expect, each checked on the step that owns it, like the checks there today:

- the Reply Plan was shown the Agenda (the Exploration's open need was in its input);
- the Reply Plan picked the aimed Curiosity, or picked none (for the must-not-ask cases);
- the aim, when it matters: which open need (unclear story, missing part of life, counter-test) and which way (story follow-up, "would it have gone differently with…", "this week, notice when…", Thought Experiment);
- the reply, through Judge rules: it asks the aimed question in its own words, as one question; it never says the Pattern Type's name, its if/then or a clinical word; it never quotes the User's earlier words back as evidence.

**B. The Tagging Eval can say an aimed Curiosity was asked.** A Tagging case can give unclear Observations the made-up User already has and mark one as asked about in this Conversation by an aimed Curiosity. The real tagging step is then shown it, as it is for a real User, and may answer `settled`. The case expects each such story to end clear (for which Pattern Type and direction) or to stay unclear. The result shows it beside the Observations kept and dropped.

**About 10 starting cases**, drafted by Claude for the owner to correct, in the existing seed files:

- Understanding, about 7: one per open need (unclear story, missing part of life, counter-test); a Thought Experiment for a look-alike pair; two Explorations where only the top one may be asked; and must-not-ask moments (the User is struggling; they brushed the last one off or asked to drop it; the last Conversation already tried, so not two in a row).
- Tagging, about 3: an answer that settles the unclear story for one of its two Pattern Types; an answer that says nothing either way, so it stays unclear; an answer that brushes the question off.

Update `docs/pattern-evals/README.md` (what these cases show and can't), `evals/README.md` (the new case fields and how to read the checks) and the "Built" notes in `docs/pattern-pipeline/README.md`.

This adds form fields to two Eval case forms. The forms are drawn from the case shapes (ADR-0014), so no new markup is expected. Read `web/design/README.md` first. If a result needs a part or words no reference shows (for example a "settled" row on the Tagging result), stop and ask the owner for the reference before building it.

Evals cost money: remind the owner and show the estimate before any run. An Understanding Message is about 4,500 tokens and a Tagging case about 8,000, so the new cases are a few cents; run only them (`make eval CASES=...`), never the whole Evals.

## Acceptance criteria

- [ ] An Understanding case can give its made-up User suspected Patterns with their Observations and earlier tries, and the Agenda and aimed Curiosity it starts with are written by the real Agenda code
- [ ] A Message can expect that the Reply Plan was shown the Agenda and that it picked the aimed Curiosity or none, and, when given, which need and way it aimed at; a failed check names its step
- [ ] Judge rules check that the reply asks the aimed question without the Pattern Type's name, its if/then, a clinical word or the User's quote
- [ ] A Tagging case can mark an unclear story as asked about by an aimed Curiosity, and passes only when it ends clear or stays unclear as expected; the result shows which
- [ ] About 7 Understanding cases and 3 Tagging cases are seeded, covering each open need, a Thought Experiment, two Explorations at once, the must-not-ask moments, and a settled, a not settled and a brushed-off answer
- [ ] Admins can add and edit the new fields on the Dashboard case forms, and a save that doesn't fit is refused beside the field
- [ ] The existing Understanding and Tagging cases still read, save and run unchanged
- [ ] The estimate is shown before the run, and the new cases were run once with the real model with the owner's go-ahead
- [ ] `docs/pattern-evals/README.md` says what these cases can and can't show, and `evals/README.md` explains the new fields
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Where to start

- The Understanding Eval: `src/companion/core/evals/understanding_eval.py`, its case and expectations in `core/evals/cases.py` (`EvalMemory`, the expectation with `curiosity_raised`), its form in `core/evals/case_shapes.py` (`UNDERSTANDING_SHAPE`), made-up memory in `core/evals/made_up_memory.py`, seed `src/companion/seed/evals/cases/understanding.yaml`.
- The Tagging Eval: `src/companion/core/evals/tagging_eval.py`, `TAGGING_SHAPE`, seed `tagging.yaml`; the step it runs is `PatternTagger.tag_from` in `core/observations.py` (`read_settled_answer`, `plan_settled`).
- The Agenda: `core/agenda.py` (`AgendaKeeper`, `AgendaReader`, `open_needs`, `aimed_question`); what the Reply Plan is given and its logged shape are in `core/reply_plan.py` and `core/reply_service.py`.
- Turning the Features on for a made-up User: `turn_pattern_noticing_on` and `turn_pattern_sharing_on` in `src/companion/adapters/evals/in_process_companion.py` (exploring alone will need its own step, since sharing must stay off here).
- Tests to copy from: `tests/test_explorations.py` (the flow with a scripted model), `tests/test_eval_runner.py` (Understanding and Tagging runner tests), `tests/test_eval_cases.py`.

## Decisions already made (owner, 25 Nov 2026)

- Extend the Understanding and Tagging Evals; no new Eval kind.
- One issue for both halves.
- About 10 starting cases, drafted by Claude, corrected by the owner later (as with the Tagging cases).

## Out of scope

- A model that plays the User over several Conversations, and tuning the Agenda's prompts. Both are issue `26-a-model-plays-the-user-and-tuning-the-agenda.md`, which the owner will grill first.
- Changing the Agenda's rules, prompts or numbers. If a case shows the Reply Plan or the reply doing the wrong thing, log it in `20-findings-for-the-owner.md` and add a note under Comments in issue 26; don't tune the prompt in this issue.
- Whether an aimed question leads to a true Pattern. Only real use shows that.

## Blocked by

- none (issues 04, 05, 11 and 14, which it builds on, are archived)

## Comments
