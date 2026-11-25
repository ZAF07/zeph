# 23 — Situations vary on more than people: event, setting, place, time, mood

Status: needs-info
Track: A
Blocked by: none (needs a grilling session first, see below)

## Parent

`.scratch/pattern-pipeline/PRD.md` (the Agenda and Explorations; decision 14 in `.scratch/pattern-pipeline/grill-decisions.md`). Design: `docs/pattern-pipeline/README.md`. Raised by the owner on 25 Nov 2026, after issue 05.

## Needs a grilling session before any solution

Don't plan or build this yet. Run `/grilling` (or `/grill-with-docs`) with the owner first, and record the decisions here and in `CONTEXT.md` and ADRs. Only then write the plan and set this to `ready-for-agent`. Open questions for the grill are listed below.

## The problem

People act differently depending on the mix they are in: who is there, what is happening, where, when, and how they feel. Zeph should find out *which mix* sets a Pattern off, and which doesn't. That is what gives a User real value ("you go quiet with people above you at work when you're tired", not just "you go quiet").

Today Zeph mostly varies **one thing: the person**.

- An Exploration's "would it differ" way only swaps the person: "would it have gone differently with someone else, like a friend / a colleague / family / a partner" (`other_person`, `aimed_question` in `src/companion/core/agenda.py`).
- A missing "part of life" is only home, work or with friends, and is always asked with a person attached.
- A counter-test asks "would you have done the same with someone else".
- An Observation's tags are relationship, power, setting (home, work, social, online) and stance (`SituationTags`). The day is kept. There is no tag for the kind of event, the place beyond those three settings, the time of day or week, or the User's mood. The event lives only in the free-text context line.
- Scoring counts a situation as a Life Thread, or the same person and setting. "Anyone would act the same" (`anyone_would_when`) can match only those tags.

## What the owner wants

Variables beyond people, mixed together:

- **Event**: what is happening, e.g. a disagreement, a request, praise, a deadline, a change of plan.
- **Social setting**: alone with one person, in a group, in public, online.
- **Place**: home, work, out, travelling.
- **Time**: time of day, day of week, busy or quiet periods.
- **Mood**: how the User felt going in, e.g. tired, stressed, calm, low.
- Others the grill may find: stakes, power, how close the person is.

Zeph should learn which of these, and which mixes, make a Pattern show up or not show up, and use that to aim its questions and narrow a Pattern ("with seniors when you're tired, not with friends").

## Open questions for the grill

1. Which variables, and what fixed list of values for each? Tags must come from closed lists so code can check them (decision 10).
2. Who fills each in? The tagging model from the Conversation, code (e.g. time from when the text was sent; mood from the Understanding's read), or both? What if a story says nothing about one?
3. Time and mood: when the story happened, or when it was told? A story told on Sunday night about Monday morning.
4. How does Zeph choose what to vary next? One variable at a time, the one least covered by the Pattern's evidence so far, or the one that best splits for and against?
5. New Exploration needs or ways, such as "not seen in a group yet" or "only seen when tired"? How do they sit next to today's unclear / missing part of life / counter-test, and the least-pushy way order?
6. Scoring: does a different mix count as a different situation? Should "anyone would act the same" match on the new tags? Inside one situation, only the strongest Observation per person counts, up to 3 people (`people_per_situation`): should the same person in a different mix (tired or calm, alone or in a group) count apart, so the cap is on mixes rather than people?
7. Narrowing: how does a Pattern record the mix it holds in, and how is that shared (issue 08) and tested with a Prediction (issue 09)?
8. Thought Experiments: should they also say which variable they vary, so code can pick one that changes the missing variable?
9. Privacy and care: mood and time can be sensitive. What may be kept and shown under "Things you said that Zeph kept"? Any exclusions?
10. Cost and evals: more tags means a longer tagging prompt and more ways to be wrong. What does the Tagging Eval (issue 14) need, and what do existing Observations get (left empty, or tagged again)?
11. Migration: Observations already kept have no new tags. Leave them empty, or re-tag?

## Acceptance criteria

To be written after the grill.

## Comments
