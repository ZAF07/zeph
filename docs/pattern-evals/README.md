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

## The three layers

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

### 3. The Whole-pipeline Eval

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
    run can be all passes and find nothing: read "true Patterns found".
  - A User who answers back. The texts are a script: they don't answer
    Zeph's questions, so an aimed Curiosity, a Thought Experiment or a
    shared Pattern never gets a real answer. The counter-test is met by a
    scripted "it doesn't happen with…" story, not by Zeph asking.
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

## How to run the Whole-pipeline Eval

It costs far more than the other Evals: every text is a full reply (the
Safeguard, Understanding, Reply Plan and reply calls) and every Conversation
a full Conversation end (about ten calls). Remind the owner and show the
estimate before any run. Until a case has run once its estimate is a rough
400,000 tokens in and 30,000 out. Five cases can pass the Eval run token
limit (1,000,000 to start; Admin → Evals → Model Prices), and the run then
stops between Conversations, so raise the limit first or run one case.

Dashboard: Admin → Evals → New run, tick Whole pipeline (or open it and pick
single cases), read the estimate, Start run. Each result shows "Became ready
or shared" and "True Patterns missed". Add a Variant to try another gate
number or prompt on the same Users. Terminal: `make eval
EVALS=whole_pipeline`, or `make eval CASES=ordinary-fortnight`; a plain
`make eval` leaves this Eval out. Cases are edited on Admin → Evals → Cases
→ Whole pipeline; the seed is
`src/companion/seed/evals/cases/whole_pipeline.yaml`, drafted by Claude for
the owner to correct.

## How to run the Tagging Eval

Dashboard: Admin → Evals → New run, tick Tagging (or pick single cases),
read the estimate, Start run. Each result shows Expected, Kept by code and
Dropped by code. Terminal: `make eval EVALS=tagging`, or
`make eval CASES=conf-yes-to-sister-then-resents`. Cases are edited on Admin
→ Evals → Cases → Tagging; the seed is
`src/companion/seed/evals/cases/tagging.yaml`. How to correct the drafted
cases and add your own: `adding-tagging-cases.md`.
