# Pattern Evals: what they can and can't show

How the Pattern pipeline (`docs/pattern-pipeline/README.md`) is tested, and how
far to trust each test. Read this before reading a Tagging or Whole-pipeline
Eval score as "Zeph's Patterns are right".

**Evals cost money.** Every run calls the real model. Before any run, remind
the owner and show the estimate: the Dashboard's New run page shows it before
Start run, and `make eval` prints it first. A full Tagging run of the first
44 cases, with three Pattern Types, was estimated at about 308,000 tokens in
and 40,000 out, about S$0.18 at the prices of 24 Nov 2026. The catalog now
has fifteen Pattern Types, all sent with every tagging call, and the seed 68
cases, so a full run costs several times that: read the estimate.

## The four layers

### 1. Code: scoring, the gate and state moves

Scoring (points per sign, kind of evidence, unclear, half-life, situations,
people per situation), the state moves (noticed, suspected, closed, and later
ready) and the checks on each Observation are pure code with ordinary tests
in `make check`. Free, run on every change.

- **Shows:** the rules do what the design says, every time, for every input
  the tests cover.
- **Can't show:** whether the numbers are right. 2 situations and 100 points
  for "suspected" are first guesses (`.scratch/pattern-pipeline/grill-decisions.md`,
  decision 29). A test proves the rule, not that the rule fits people.

### 2. The Tagging Eval

Everything downstream trusts the tagging step, so it has its own Eval kind
(`tagging`, in `evals/README.md`). A case is a made-up ended Conversation,
the Life Threads it touched, and the Observations expected: Pattern Type,
for or against, unclear (two look-alikes) or not, anyone-would-do-it
(situational) or not. The real tagging step runs on it with the whole
Pattern Catalog, code checks what it wrote, and the case passes only when
the Observations kept are exactly the ones expected. The seed has 68 cases:
44 over the first three Pattern Types (clear, against, unclear, nothing to
tag and anyone-would-do-it), and one for and one against each of the twelve
added later.

- **Shows:** whether the step finds the Pattern Type a careful reader would,
  says for or against right, says "unclear" when two look-alikes fit, keeps
  quiet when there is nothing to tag, and whether its quotes and tags
  survive code's checks. It catches a prompt, model or catalog change that
  makes tagging worse.
- **Can't show:**
  - That the expected answers are right. They were drafted by Claude and
    to be corrected by one person, the owner, once the PRD is built
    (`adding-tagging-cases.md`). One rater's labels are one opinion.
  - How often it is right on real Users. Made-up Conversations are cleaner
    and more on-topic than real ones; real people hint, joke and contradict
    themselves.
  - Anything about Pattern Types not in the catalog yet, or about how tags
    other than "anyone would" are filled in (relationship, power, setting,
    stance and kind of evidence are only checked against their lists).
  - "Anyone would" for ACH.WORTH.PERF and CTRL.UNCERT.PLAN: their "anyone
    would" (high stakes, a real crisis) can't be written as tags, so code
    never marks theirs situational. Those cases expect the step to say
    nothing, or a sign against.

#### Unclear stories an aimed Curiosity asked about

A Tagging case can also give unclear Observations the made-up User already
has and mark one as asked about in this Conversation by an aimed Curiosity
(issue 25). The real tagging step is shown it, as for a real User, and the
case passes only when the story ends as expected: clear for one of its two
Pattern Types, or still unclear. The seed has 3: an answer that settles
it, one that tells nothing either way, and one that brushes the question
off.

- **Shows:** whether the step settles a story when the answer really
  tells, and leaves it unclear when it doesn't.
- **Can't show:** that the answers sound like real ones. Claude wrote both
  Zeph's question and the User's answer, so the settling answer says its
  reason plainly. Real answers are shorter and sideways. It also can't
  show the question was a good one: Zeph's line in the case is typed, not
  written by the reply.

### 3. The Agenda cases in the Understanding Eval

The Agenda's rules are code, with ordinary tests. What only a real model
can show is tested by cases in the Understanding Eval (`understanding`, in
`evals/README.md`), with keys starting `agenda-` (issue 25). A case gives a
made-up User suspected Patterns: Observations and the tries already made.
Setup saves them as real rows and runs the real scoring and Agenda code, so
the Agenda and the aimed Curiosity are the ones code writes. One Message is
then sent, and checked on the Reply Plan (was it shown the Agenda, did it
bring up the aimed Curiosity, which need and way) and, by the Judge, on the
reply (does it ask the aimed question as one question in its own words,
without naming the Pattern Type, its if/then, a clinical word or the
User's own quote). The seed has 9: one per open need (unclear story,
missing part of life, counter-test), a Thought Experiment, two
Explorations at once, and four must-not-ask moments (struggling, brushed
off, asked to drop, the last Conversation already tried).

- **Shows:** whether the Reply Plan picks the aimed Curiosity at an easy
  moment, whether the reply words it well and keeps the Pattern unnamed,
  and whether Zeph leaves the story alone when it shouldn't ask. It
  catches a Reply Plan or Reply prompt change that makes Zeph stop asking,
  ask clumsily, name a Pattern, or push after a brush-off.
- **Can't show:**
  - Timing in a real Conversation. Each case is one Message at a moment
    Claude chose as fitting or not. Whether Zeph picks good moments over a
    long, messy Conversation isn't tested.
  - What the User answers, or that the question leads to a true Pattern.
    Nobody answers here. A model that plays the User is issue 26.
  - The must-not-ask rules themselves. Whether an aimed Curiosity is
    offered after a brush-off, a drop or a try yesterday is decided by
    code and covered by tests; here code has already taken it away. These
    cases show what the model does with what is left: the Agenda is still
    shown after a brush-off or a try yesterday, and the reply must not go
    back to the story on its own.
  - That the Judge's rules are right. They were drafted by Claude for the
    owner to correct, and "names a pattern" is a judgement call.
  - A steady result. One Message, one run. Use Repeats before trusting a
    change.

### 4. The Whole-pipeline Eval

It has its own Eval kind (`whole_pipeline`, in `evals/README.md`). A case is a
made-up User with hidden true Pattern Types and a script of several
Conversations, with the clock moved between them. Every text goes through
the real reply path and every Conversation ends through the real
Conversation-end steps, with Pattern noticing, exploring and sharing on. The
result lists each Pattern that became ready or was shared and whether it is
a true one, and the true ones missed with where they stopped. A case passes
when every ready Pattern is a true one. Target for a run: at least 70% of
ready Patterns true. The seed has 5 made-up Users: one true Pattern with a
"not with my partner", two true look-alikes, none, one true whose look-alike
is not, and one true beside a single story of its look-alike.

- **Shows:** the pieces work together: replies, Life Threads, tagging,
  scoring, the Agenda, the gate and sharing move the right Patterns and
  leave the rest. It catches a change that breaks the chain (nothing ever
  becomes ready) or opens it too wide (a Pattern becomes ready from one
  story, or a look-alike does).
- **Can't show:**
  - Truth. A model playing a User and a model tagging them tend to agree:
    the player writes the Pattern the way a model expects it to sound, and
    the tagger hears it. Here the player is Claude, who drafted every text
    with the Pattern Catalog open. So this layer catches breakage, not
    whether Patterns are true or new to real people.
  - That 70% means anything for real Users. Five scripted Users give a
    handful of ready Patterns, so one more or one fewer moves the share a
    lot. Read each case, not only the share.
  - Missed Patterns as failures. A case with nothing ready passes, so a
    run can be all passes and find nothing: read "true Patterns found". A
    Conversation-end step that fails is logged and skipped, as in the live
    app, so scoring or the gate breaking part-way shows only as fewer
    Patterns found (the case is an Error only when the Conversation isn't
    processed at all or the tagging step didn't run).
  - A share for the whole run on the Dashboard. The terminal report prints
    it against the 70% target; the Dashboard shows each case's Patterns and
    "true Patterns found", and the share is left to add up.
  - A User who answers back. The texts are a script: they don't answer
    Zeph's questions, so an aimed Curiosity, a Thought Experiment or a
    shared Pattern never gets a real answer. The counter-test is met by a
    scripted "it doesn't happen with…" story, not by Zeph asking. Whether
    the aimed question is asked well, and an answer read right, is tested
    apart: see "The Agenda cases" and "Unclear stories" above.
  - Sharing by Check-in, Prediction follow-ups, or anything over weeks: the
    made-up User has Check-ins off and a script covers about two weeks, so
    fading and the wait before a Check-in shares are never reached.
  - A steady result. Zeph's replies and the tagging vary from run to run,
    so the same case can find a Pattern one day and miss it the next. Use
    Repeats before trusting a change.

## What only real use can show

Whether a Pattern is true and new to the person comes only from real
Prediction outcomes and how people react when a Pattern is shared. No Eval
replaces that.

## What must be done later

- **A second rater.** Someone other than the owner labels the same cases
  without seeing the first labels; where they disagree, the case is unclear
  or the Pattern Type's description is. Report how often the two agree.
- **200 labelled Observations.** Grow the Tagging cases toward 200, with
  real-sounding mess (hints, jokes, contradictions), more of each Pattern
  Type, and the twelve Pattern Types still to come (issue 15).
- **A score that means a probability.** Today a score is points. Once
  Predictions run (issue 09), compare scores with how often Predictions come
  true, and turn the score into a chance that the Pattern holds.
- **A psychologist's review.** Before Patterns are shared widely, someone
  trained reads the catalog, the signs and a sample of tagged Observations,
  and says where they are wrong or harmful.

## First Whole-pipeline results (25 Nov 2026)

Three case runs, on the live settings unless said:

- `ordinary-fortnight` (no true Pattern): nothing became ready. Pass.
- `folds-with-sister-and-friends` (CONF.AVOID.BELONG): it became ready after
  5 Conversations. Pass, 1 of 1 true found.
- The same case with "Situations to be ready" at 9: it stayed suspected,
  stopped by situations. Pass, 0 of 1 found.

So the chain works end to end and a gate number moves the result as it
should. This says nothing yet about the 70% target: the look-alike cases
(`goes-quiet-and-says-fine`, `cannot-stand-waiting`, `never-arrives`) have
not been run, and no case has had a Pattern shared.

## First Agenda results (25 Nov 2026)

The twelve cases were run once with the real model: 9 passed, 3 failed,
about 108,000 tokens in and 22,000 out, S$0.075. The Reply Plan picked the
aimed Curiosity for each open need and for the Thought Experiment, and left
the story alone in all four must-not-ask cases. All three Tagging cases
passed: the plain answer settled the story, and the other two left it
unclear. What failed: one reply said the User's own words back when it
asked ("You said yes the moment she asked"); with two Explorations the
Reply Plan asked neither; and the first struggling Message was taken by the
Safeguard as a crisis, so that case was rewritten (it then passed). One run
proves little: use Repeats. The findings are in
`.scratch/pattern-pipeline/issues/20-findings-for-the-owner.md`, section 25.

## How to run the Whole-pipeline Eval

It costs far more than the other Evals: every text is a full reply (the
Safeguard, Understanding, Reply Plan and reply calls) and every Conversation
a full Conversation end (about ten calls). Remind the owner and show the
estimate before any run. The shortest case (`ordinary-fortnight`, 12 texts in
4 Conversations) used 208,000 tokens in and 76,000 out, S$0.20, and took 8
minutes (25 Nov 2026). Until a case has run once its estimate is a rough
300,000 tokens in and 110,000 out. The 5 cases together pass the Eval run
token limit (1,000,000 to start; Admin → Evals → Model Prices), and the run
then stops between Conversations, so raise the limit first or run one case.

Dashboard: Admin → Evals → New run, tick Whole pipeline (or open it and pick
single cases), read the estimate, Start run. Each result shows "Became ready
or shared" and "True Patterns missed". Add a Variant to try another gate
number or prompt on the same Users. Terminal: `make eval
EVALS=whole_pipeline`, or `make eval CASES=ordinary-fortnight`; a plain
`make eval` leaves this Eval out. Cases are edited on Admin → Evals → Cases
→ Whole pipeline; the seed is
`src/companion/seed/evals/cases/whole_pipeline.yaml`, drafted by Claude for
the owner to correct.

## How to run the Agenda cases

They are ordinary Understanding and Tagging cases, so run only them by key.
Terminal: `make eval
CASES=agenda-unclear-story-asked,agenda-missing-part-of-life-asked,agenda-counter-test-asked,agenda-thought-experiment-asked,agenda-two-explorations-top-one-asked,agenda-not-asked-while-struggling,agenda-not-asked-after-brush-off,agenda-not-asked-after-asked-to-drop,agenda-not-asked-two-conversations-in-a-row,unclear-story-settled-by-the-answer,unclear-story-answer-tells-nothing,unclear-story-question-brushed-off`.
Dashboard: Admin → Evals → New run, pick those cases, read the estimate,
Start run. An Understanding Message is about 4,500 tokens and a Tagging
case about 8,000, so all twelve are a few cents. Cases are edited on Admin
→ Evals → Cases → Understanding (Made-up User Memory → Suspected Patterns)
and → Tagging (Unclear stories they already have).

## How to run the Tagging Eval

Dashboard: Admin → Evals → New run, tick Tagging (or pick single cases),
read the estimate, Start run. Each result shows Expected, Kept by code and
Dropped by code. Terminal: `make eval EVALS=tagging`, or
`make eval CASES=conf-yes-to-sister-then-resents`. Cases are edited on Admin
→ Evals → Cases → Tagging; the seed is
`src/companion/seed/evals/cases/tagging.yaml`. How to correct the drafted
cases and add your own: `adding-tagging-cases.md`.
