# 23 — Situations vary on more than people: event, setting, place, time, mood

Status: completed (the record of decisions; no code was built from this file. Built through issues 41 to 44, all archived)
Track: A
Blocked by: 41, 42, 43, 44

Grilled with the owner on 25 Nov 2026: see "Decisions from the grill" below, ADR-0031, and **Condition** and **Approach** in `CONTEXT.md`. Built through four issues: 41 (Conditions are tagged), 42 ("anyone would" on Conditions), 43 (Zeph asks about a missing Condition; "way" becomes Approach) and 44 (narrowing and sharing). Issue 40 (directness also sets how Zeph asks) follows 43.

## Parent

`.scratch/pattern-pipeline/PRD.md` (the Agenda and Explorations; decision 14 in `.scratch/pattern-pipeline/grill-decisions.md`). Design: `docs/pattern-pipeline/README.md`. Raised by the owner on 25 Nov 2026, after issue 05.

## Needs a grilling session before any solution (done, 25 Nov 2026)

Kept as written before the grill. The answers are under "Decisions from the grill".

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

## Decisions from the grill (25 Nov 2026, owner: Zaf)

Each has what was decided, why, and what was turned down, so it can be revisited later.

**D1. The new tags narrow a Pattern Type's "if" for each User. They don't describe the whole situation.**
- Decided: a Pattern Type gives the event ("Disagreement with a valued other"). The new tags say under which conditions that event sets the Pattern off for this User ("with people above you, in a group, when worn out; not one-to-one with friends"). This extends today's narrowing, which only uses kinds of people.
- Why: this is the "if situation, then behaviour" signature of Mischel and Shoda (1995), the framework Zeph follows. It fits ADR-0024 (code tests against the catalog).
- Turned down: tagging every situation in full so Zeph could find patterns the catalog lacks. That is the parked "catalog suggestions by a model" work.

**D2. Event is not a tag.**
- Why: every Pattern Type's "if" already names the event, so an Observation "for" it means that event happened. A tag would repeat it and add ways to be wrong.

**D3. The conditions are ranked by how "psychologically active" they are, not treated as equal.**
- Order: audience, stakes, state going in, then place and time last. Event dropped (D2).
- Why: Mischel and Shoda found that what a situation means to the person (who, what they did, what is at stake) predicts behaviour, and nominal features (the room, the clock) don't. Mood is not part of the situation in their model: it is a state the person brings in, which changes how the situation lands.
- Exact lists of values: see D7 onward (still being decided).

**D4. Zeph reads conditions for free, and never guesses.**
- Decided: the tagging step fills a condition only when the story says it. Not said means empty.
- Why: a guessed tag would narrow a Pattern on something the User never said.

**D5. Zeph never asks just to fill a blank. Code decides when a condition is worth asking about.**
- Decided: an empty tag on a story is not a reason to ask. Zeph asks only when the answer would change a suspected Pattern. Code works this out; the model never does. No new question budget: these questions use today's ways and limits (fewest replies between Curiosities, story follow-ups per Conversation, never two Conversations in a row, backing off after brush-offs).
- Why (owner): Zeph must be proactive about finding conditions out, but must never sound like an interrogator. Better-aimed questions, not more questions.
- Accepted cost: nothing is asked about conditions while a Pattern is only noticed, so conditions are learned slowly at first.
- Turned down: asking earlier than suspected. Asking about conditions for something seen once is where interrogation starts.

**D6. A coverage table per Pattern, and one rule for a "missing condition" need. To be tried, then tuned.**
- Decided: for each suspected Pattern, code works out a coverage table from its Observations: for each condition and each value, how many clear stories for, clear stories against, or none. It is worked out each time, never stored, so it can't drift from the evidence. What was asked, when, which way and how it went is already stored as the Exploration's tries.
- A condition's value becomes an open need only when all hold: (1) one-sided: at least 2 clear stories for the Pattern have that condition known and all share one value; (2) the other value has no clear story, for or against; (3) one at a time: only the most one-sided condition is a need; (4) asked once per value: a useful answer closes it, and it rests after the usual tries with nothing.
- Order of needs: unclear story, then counter-test, then missing condition. Counter-test moved ahead because the ready gate requires it, and a counter-test often answers a condition too.
- Today's "missing part of life" need (home, work, with friends) is folded in: it becomes one condition under this rule, not its own need.
- The answer is stored as an ordinary Observation with the condition tagged. An answer against narrows the Pattern, as people tags do today.
- Why (owner): Zeph must "keep tabs" on what is known and missing for each Pattern, and remember what it asked, so asking is reliable and never random.
- Open to tuning: the "at least 2" bar and the order of needs are first guesses.

**D7. The term is "Condition".**
- Decided: a Condition is a tag on an Observation saying under what circumstances it happened. Relationship, power, stance and setting are Conditions too, so one word and one rule cover all of them.

**D8. The lists.**
- Unchanged: relationship, power, stance, setting (home, work, social, online). Setting is the "place" of this issue.
- New, **audience**: one-to-one, group, in front of others (people watching who aren't part of it, e.g. a presentation or a row in public).
- New, **stakes**: low, high (high: something that matters to the User could be lost, e.g. a job, a relationship, money, standing). Also lets ACH.WORTH.PERF's and CTRL.UNCERT.PLAN's "anyone would" (high stakes) be put as tags, which they can't be today.
- New, **state going in**: worn out, under pressure, low, steady. How the User was before it happened, not how they felt after.
- No time tag. Why: a story rarely gives a time, and when time matters it is nearly always a stand-in for state ("late at night" means worn out). State is tagged as of when the story happened, from the story's own words, never from when it was told and never from the Understanding's read of the User's mood while telling it.
- No "out" or "travelling" in setting. Why: too rare to reach the bar in D6.
- Short lists on purpose. Why: with 4 values a condition can show a trend from a handful of stories; with 10 it never would.
- Known risk: the tagging model mixing up "state going in" with how the User felt after. The Tagging Eval must cover it.

**D9. Narrowing uses every Condition, with guards so a Pattern can still be shown wrong.**
- Decided: (1) each Condition is looked at alone, as today; no stored combinations, the wording joins single narrowings; (2) a Condition narrows only when at least 2 clear stories for share the "holds" side with that Condition known (today 1 is enough); (3) at most 2 narrowings per Pattern, the two with the most stories behind them; evidence against that those don't explain counts against the Pattern in full; (4) the shared wording says where it shows and where it doesn't, as today.
- Why: with seven Conditions, almost any story against differs from the stories for on something. If each difference could narrow, all evidence against would be explained away and the gate's "tested against itself" check would mean nothing.
- Accepted cost: Zeph will sometimes say less than it could.
- Turned down: stored combinations ("above you AND worn out" as one tested claim). They need far more stories than a User gives.
- Open to tuning: the bar of 2 and the cap of 2.

**Owner's principle (25 Nov 2026), to read every decision here against.**
Zeph is not there to prove Patterns correct. It is there to help people become more self-aware, so they can work on it with or without Zeph. A reflection feature is planned, where Zeph guides a User to reflect on their Patterns. So the guards above are there to keep what Zeph claims honest, not to make proof the goal; what Zeph hasn't seen yet is useful to the User too, as something to notice for themselves.

**D10. Sharing: narrowings as today, plus one thing Zeph hasn't seen, said as an open question.**
- Decided: (1) narrowings are said as today, now for any Condition; (2) code hands the reply at most one gap from the coverage table, said as something Zeph doesn't know ("I've only heard about this in meetings. I don't know if it's the same when it's just the two of you"), never as a claim; (3) state is said gently and in the User's own words where possible ("you mentioned being worn out both times"), never "you do this when you're low"; (4) the Prediction stays as it is, set inside the narrowing; (5) nothing is built for the reflection feature now, since the coverage table is worked out from Observations and can be read later.
- Why: the owner's principle. An honest "I don't know" needs no proof and hands the noticing to the User. What they say back is tagged like any story, so the gap fills with no extra question.

**D11. Conditions don't change how evidence is counted. "Anyone would act the same" can match them.**
- Decided: (1) a situation stays one Life Thread (with none, the same person and setting); a different mix inside one Thread is not a new situation; (2) the cap inside a situation stays per person, not per mix; (3) in scoring, Conditions only narrow (D9): they never add points or situations; (4) `anyone_would_when` can match audience, stakes and state, so ACH.WORTH.PERF and CTRL.UNCERT.PLAN get "high stakes" as tags; each catalog change is a new version approved by the owner (ADR-0025).
- Why: the situations count shows a Pattern turns up in separate parts of a life. If mixes counted apart, richer tags alone would make Patterns ready sooner on the same evidence.
- Known limit: stories kept before this have no stakes tag, so they don't match the new "anyone would" rules and keep their weight (see the decision on old Observations).

**D12. How Zeph asks about a missing Condition.**
- Decided: (1) three ways, least pushy first: story follow-up ("was it just the two of you?"), then "would it have gone differently if…" for any Condition, then "this week, notice whether it's the same when…"; (2) no Thought Experiment for Conditions for now; (3) Zeph never names a state first: for state it may only ask openly ("how were you doing going into that?"), only as a story follow-up or a "notice", and offers no state the User hasn't said; (4) a "would it differ" answer is a "what if" answer, so weak evidence, but it fills the gap and closes the need; (5) code gives the Condition and value to learn, the model words it or leaves it when the moment is wrong.
- Why (3): a question that names a state leads the answer ("would it be different if you weren't so tired?" invites a yes).
- Parked (2): the 31 Thought Experiments are written to tell look-alikes apart. Marking each with the Condition it varies, and writing new ones, is its own work.

**D13. "Way" is renamed "Approach".**
- Decided: how an Exploration asks is its Approach. In `CONTEXT.md` now; `ExplorationWay` and the stored column are renamed with this issue's code work (a small migration, to be called out in the PR). D12's "ways" are Approaches.
- Why (owner): "way" is hard to understand and easy to miss as a term.
- Turned down: question style ("notice this week" isn't a question), method (sounds like code), angle (vague).

**D14. Privacy rules for state.**
- Decided: (1) state is kept only when the User's own words in that Conversation say it, never from the Understanding's read of their mood or a Day Summary; (2) the list stays everyday words, no clinical terms ("low" is a low day, never a diagnosis); (3) nothing new is shown under "Things you said that Zeph kept": Zeph's note already says what was going on, and no other tag is shown; (4) it goes when its quote goes (deleting the quote, a Pattern, a Life Thread, Delete My Data); no separate store of states; (5) Admins never see it, not even as counts; (6) Observations from a Conversation with a Safeguard Event get no state tag: a crisis is not a Condition.
- Turned down: a User switch to stop state being tagged. Pattern noticing can already be turned off and any quote deleted; a second switch is a setting few would find.

**D15. The directness setting will also set how Zeph asks. Its own issue: 40.**
- Decided: directness changes where an Exploration starts and how long it waits after a try with nothing (gentle: no "would it differ", longer wait; direct: starts at "would it differ", shorter wait). Backing off, struggling, never naming a state, never two Conversations in a row and the ready gate stay fixed for everyone. It applies to every Exploration need. Not built in this issue: see `40-directness-also-sets-how-zeph-asks.md`.
- Why (owner): the setting should also affect how pushy Zeph is. This changes decision 7 of the first grill, which kept directness to the Read only.
- In this issue, before 40 is built: the Approach order is the same for every User, and only the wording follows directness (the reply already knows it).

**D16. No old Observations to deal with.**
- Fact (owner): the pattern pipeline hasn't been deployed or used, so no User has kept Observations. No data migration and no tagging again. An Observation made earlier in a development database just has the new Conditions empty, which D4 already allows.

**D17. How it is tested.**
- Pure code tests carry most of it: the coverage table, the "worth asking" rule (D6), the order of needs, narrowing with its bar and cap (D9), "anyone would" on the new Conditions (D11), no state tag after a Safeguard Event (D14).
- The Tagging Eval learns to check Conditions: a case may state the Conditions it expects, "must be empty" included. About 10 new cases: each new Condition said, so tagged (3); nothing said, so all empty (2); the User says how they felt after, so state stays empty (2); a high-stakes story for ACH.WORTH.PERF and CTRL.UNCERT.PLAN, so situational (2); two people and a group, audience against relationship (1).
- The Understanding Eval gets 3 Agenda cases: a one-sided Pattern gets a question aimed at the unseen value; one that isn't one-sided gets none; a state gap is asked openly with no state named.
- The Whole-pipeline Eval gets no new case now: it costs the most and its scripted Users never answer questions.
- Cases are drafted by Claude for the owner to correct; that correction is an owner task, not an acceptance criterion. Evals cost money: give the estimate before any run, and run only the new cases while building.

**Defaults picked without asking (say so if any is wrong).**
- One value per Condition on an Observation. When a story gives two for one Condition (worn out and under pressure), the model picks the one the story leans on; when it can't, the Condition is left empty.
- The new bars (2 stories to be one-sided, 2 stories to narrow, 2 narrowings per Pattern) are Platform Settings with hints in the Patterns section, overridable in Eval Variants, like the other Pattern numbers.
- Admins see nothing new about a User. The trace page's "Observations tagged" and "Dropped by code" stay as they are; an Observation with a Condition outside its list is dropped, as for today's tags.
- The other-side model call is given every narrowing, as today.

**D18. Recorded in an ADR, built as four issues, no PRD of its own.**
- ADR-0031 holds the choices that are hard to undo (D1 to D6, D9, D11, D14). The lists, the rename and the tests are easy to change, so they have no ADR.
- No own PRD. Why: this extends the pattern-pipeline PRD (decisions 7, 9, 10, 14 and 16 of its grill) behind the same three Features, and this file already holds what a PRD would. A PRD would be worth it for the parked parts below.

**Parked, with why.**
- Thought Experiments that vary a Condition (D12): its own writing work.
- Stored combinations of Conditions as one tested claim (D9): needs more stories than a User gives.
- A time tag (D8), and a User switch for state (D14).
- The reflection feature reading the coverage table (D10): nothing to build until that feature is designed.

## Acceptance criteria

- [x] Issues 41, 42, 43 and 44 are done and archived.

## Comments

### 26 Nov 2026 — closed

Issues 41, 42, 43 and 44 are built, checked in the running app and archived in `archive/` beside this file. Issue 40 (directness also sets how Zeph asks) is its own issue and still open. The parked parts above stay parked.

## Completion

- Completed: 2026-11-26
- Commit: 5113b328 ("Merge pattern-44-narrowing-every-condition: narrowing and sharing use every Condition", the merge that archived this file with issue 44; issues 41, 42 and 43 merged as 7f079738, d0861ccf and 72b6532c)
