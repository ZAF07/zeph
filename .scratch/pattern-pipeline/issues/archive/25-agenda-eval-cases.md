# 25 — Eval cases for the Agenda: is the aimed question asked well, and is the answer read right

Status: completed
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

- [x] An Understanding case can give its made-up User suspected Patterns with their Observations and earlier tries, and the Agenda and aimed Curiosity it starts with are written by the real Agenda code
- [x] A Message can expect that the Reply Plan was shown the Agenda and that it picked the aimed Curiosity or none, and, when given, which need and way it aimed at; a failed check names its step
- [x] Judge rules check that the reply asks the aimed question without the Pattern Type's name, its if/then, a clinical word or the User's quote
- [x] A Tagging case can mark an unclear story as asked about by an aimed Curiosity, and passes only when it ends clear or stays unclear as expected; the result shows which
- [x] About 7 Understanding cases and 3 Tagging cases are seeded, covering each open need, a Thought Experiment, two Explorations at once, the must-not-ask moments, and a settled, a not settled and a brushed-off answer
- [x] Admins can add and edit the new fields on the Dashboard case forms, and a save that doesn't fit is refused beside the field
- [x] The existing Understanding and Tagging cases still read, save and run unchanged
- [x] The estimate is shown before the run, and the new cases were run once with the real model with the owner's go-ahead
- [x] `docs/pattern-evals/README.md` says what these cases can and can't show, and `evals/README.md` explains the new fields
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

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

**25 Nov 2026, built (Claude).** Branch `pattern-25-agenda-eval-cases`.

Decisions made while building:

- The owner chose (asked 25 Nov 2026) to show a settled story on the Dashboard as a fourth part of the Tagging result, "Unclear stories", built from the result's own part, row and pill. The owner gave the go-ahead to run the new cases once, and later to run two old cases once.
- A made-up try can't be a Thought Experiment (the form offers story follow-up, someone else, notice this week). The Thought Experiment itself is always picked by the real Agenda code.
- A try "asked to drop" is saved not yet judged, so the real Agenda code judges it and rests the Exploration.
- Each Conversation a made-up try was asked in gets twice the pace's replies after it, or the pace between Curiosities would hold the next aimed Curiosity back.
- When a case gives Thought Experiments, the seeded ones are archived in the Eval database for that case.
- A Tagging case expects the Pattern Type a story ends clear for. The direction can't change when a story settles, so it is shown, not checked.
- 9 Understanding cases, not 7: brushed off and asked to drop are two cases, since code treats them differently.
- The first struggling Message ("dad's in hospital") was taken by the Safeguard as a crisis. The case was rewritten and run alone once more.

Evidence, per criterion (running app = this worktree's stack, ports 3010/8010):

1. **Made-up suspected Patterns; Agenda written by real code.** `give_made_up_patterns` runs the real `PatternScorer` and `AgendaKeeper`. Real run `1641c640`: the Reply Plan's input held "[1] Softening disagreement to protect belonging … Still to learn: …" and the aimed Curiosity "Go back to what they told you about Mei, their sister on 8 Nov 2026 …" with "Saved 13 Nov 2026", none of it typed into the case. Tests: `test_an_understanding_case_s_agenda_and_aimed_curiosity_are_written_by_real_code`, `test_a_try_already_made_lets_the_real_agenda_pick_a_thought_experiment`.
2. **Agenda shown, aimed Curiosity or none, need and way; a failed check names its step.** Real run: e.g. `PASS Reply Plan · aimed need: aimed at a counter-test`, `PASS Reply Plan · aimed way: asked by a Thought Experiment`, and `FAIL Reply Plan · aimed curiosity: brought up no aimed Curiosity, expected: brought up the aimed Curiosity` (two Explorations).
3. **Judge rules.** `never_names_a_pattern`, `no_quote_back` and one "asks the aimed question" rule per case. Real run: `FAIL no_quote_back: … 'You said yes the moment she asked'`, and passes on the others.
4. **Tagging: asked unclear story ends as expected; the result shows which.** Real run: `unclear-story-settled-by-the-answer` ended clear for CONF.AVOID.BELONG (I4) and the story not asked about stayed unclear; the other two stayed unclear. Seen on the run page in a browser at 1280 and 390: "Unclear stories", "Ended clear", "Stayed unclear", Was / Asked about / Now / Expected. Fail paths: `test_a_tagging_case_passes_only_when_its_unclear_story_ends_as_expected`.
5. **Seeded cases.** 9 `agenda-…` in `understanding.yaml` (unclear story, missing part of life, counter-test, Thought Experiment, two Explorations, struggling, brush-off, asked to drop, two Conversations in a row) and 3 `unclear-story-…` in `tagging.yaml` (settled, tells nothing, brushed off). All 12 loaded into the running stack and ran.
6. **Dashboard forms.** In a browser as an Admin: the Understanding case form showed Suspected Patterns, Tries already made, Thought Experiments and the five new expectations; an empty Sign was refused with "Needs some text." under the field, then saved once fixed. The Tagging form showed "Unclear stories they already have"; "Ends clear for: REL.MOOD.FIX" was refused with "Must be one of its two Pattern Types: CONF.AVOID.BELONG or APPR.GIVE.NEEDED" under the field, then saved once fixed. Pixel test (copy that blocks Clerk's probes, as before): `PASS AdminEvalTaggingCase 0.00%`, `PASS AdminEvalDaySummaryCase 0.00%`.
7. **Existing cases unchanged.** In a browser, `curiosity-raised-once` and `conf-yes-to-sister-then-resents` opened and saved with no change. Real run `f1e44bc1` (S$0.0178): the Understanding case passed 5 of 5; the Tagging case was shown "Unclear stories Zeph asked about in this Conversation: None." as before and failed on an extra unclear CONF.AVOID.BELONG + APPR.GIVE.NEEDED Observation, which is the failure issue 20 already lists for this very case since the catalog grew (section 15), not something this issue changed. 2,461 backend tests pass.
8. **Estimate and real run.** `make eval` printed "Estimate: 12 cases, about S$0.0740"; run `1641c640` cost S$0.0754: 9 passed, 3 failed. The rewritten struggling case then ran alone (`ee9f97a9`, pass, S$0.0057). Findings: `20-findings-for-the-owner.md` section 25, and a note under Comments in issue 26.
9. **Docs.** `docs/pattern-evals/README.md` (layer 3 "The Agenda cases", "Unclear stories", first results, how to run), `evals/README.md` (fields, reading the checks, adding cases), Built note in `docs/pattern-pipeline/README.md`.
10. **Checks.** `ruff check`, `ruff format --check`, `mypy`: clean. `pytest`: 2461 passed. Web: `pnpm lint`, `format:check`, `typecheck` clean, `pnpm test` 989 passed. The stack's images build (`make restart`).

Caveats: the real run was made before the last review fixes (an aim check now also fails when a second aimed Curiosity is brought up; made-up replies are added once per Conversation; tidier result code). Those are covered by tests, not by a second paid run. The words of the "Unclear stories" part are in no reference file (issue 20). The cases and Judge rules are Claude's drafts for the owner to correct.

## Findings for the owner

The same text is section 25 of `20-findings-for-the-owner.md`. It was added there in the main folder's working copy, not in this branch, because that file had the owner's uncommitted triage edits when this was merged.

Run `1641c640`, 12 cases once: 9 passed, 3 failed. 108,180 tokens in, 22,240 out, S$0.0754 (estimate S$0.0740). One case was then rewritten and run alone (`ee9f97a9`, pass, S$0.0057). Nothing was tuned: the prompts are issue 26's.

#### The reply says the User's words back when it asks the aimed question

- **Kind:** to decide
- **What:** `agenda-unclear-story-asked`. The Reply Plan picked the aimed Curiosity and the reply asked it as one question, but it wrote "You said yes the moment she asked", close to the kept quote ("I said yes straight away"). The Judge failed `no_quote_back`, and also `never_names_a_pattern`, calling that line "a tendency".
- **Impact:** the User can feel their words are being kept and used as evidence. The second failure looks like the Judge's rule being too wide, not Zeph naming a Pattern.
- **Suggested fix:** in issue 26, look at how `describe_story` hands the story to the reply (it gives the context line, never the quote, so the model worked the words out itself). Tighten `never_names_a_pattern` so it is only about naming a habit, not about recalling an event.

#### With two Explorations the Reply Plan asked neither

- **Kind:** to decide
- **What:** `agenda-two-explorations-top-one-asked`. Both aimed Curiosities were offered; the Reply Plan picked Just chatting with Get curious, brought up no Curiosity and gave no reason. The same kind of quiet-evening Message got the aimed Curiosity in three one-Exploration cases.
- **Impact:** one run, so it may be chance. It may also be that two "ask about a recent time at…" Curiosities fit a "nothing day" worse than a story does.
- **Suggested fix:** run it with Repeats before reading anything into it; the owner may want a Message that fits better.

#### Aimed Curiosities are offered in the order written, not in the Agenda's order

- **Kind:** risk
- **What:** the Reply Plan is told "when an aimed Curiosity's day has come, it is first among the Curiosities above". With two Explorations there are two, listed by when they were saved (`list_waiting` orders by `position`), and `plan_agenda` writes them in the Explorations' stored order, not by rank. So number 1 can be for the lower-ranked Exploration. Seen in a test of the seed case, where the order changed between runs.
- **Impact:** the model has no sure way to tell which aimed Curiosity is for the top Exploration.
- **Suggested fix:** write, or offer, aimed Curiosities in rank order. A rule change, so it is for the owner (issue 26).

#### The Safeguard took "dad's in hospital" as a crisis

- **Kind:** to decide
- **What:** the first draft of `agenda-not-asked-while-struggling` said "dad's in hospital, they think it's his heart. I can't stop shaking". The Safeguard answered with the helpline message, so the Understanding never ran. The case now uses losing a flat, which passes.
- **Impact:** a frightened User with a relative in hospital gets the crisis reply, not Zeph.
- **Suggested fix:** the owner decides whether that is wanted; if not, add it to the Safeguard Eval as a false alarm.

#### Must-not-ask is decided by code before the model sees anything

- **Kind:** risk
- **What:** after a brush-off, a drop or a try yesterday, code has already taken the aimed Curiosity away. The four must-not-ask cases passed, but what they test is narrower than it sounds: that the reply doesn't go back to the story on its own while the Agenda is still shown. The guide says so.
- **Suggested fix:** none; a wrong-moment case where the Curiosity *is* offered (a hurried or practical Message) would test the model's own judgement. The owner may want one.

#### The Tagging result's "Unclear stories" part has no reference file

- **Kind:** risk
- **What:** the owner agreed (25 Nov 2026) to a fourth part built from the Tagging result's own rows. Its words are new: "Unclear stories", "Ended clear", "Stayed unclear", "Was", "Asked about in this Conversation", "Now", "Expected", "Clear for …", "Unclear", and "N unclear story wrong" on the verdict pill. It shows only when a case has unclear stories, so `AdminEvalTaggingCase` is unchanged.
- **Impact:** no pixel test covers it; checked by eye at 1280 and 390.
- **Suggested fix:** the owner approves the words or adds them to the reference.

#### A try's made-up Conversation is given replies so the pace allows the next Curiosity

- **Kind:** risk
- **What:** the pace between Curiosities counts replies since the last one was asked. A made-up try has none after it, so the next aimed Curiosity would never be offered on the case's first Message. Setup adds twice the Admin-set number of made-up replies after each try (`add_replies_after` in `core/evals/made_up_patterns.py`).
- **Impact:** the pace rule itself is not tested by these cases.
- **Suggested fix:** none needed; the tests of the pace cover it.

## Completion

- Completed: 2026-11-25
- Commit: <filled in after the merge>
