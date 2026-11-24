# Pattern Evals: what they can and can't show

How the Pattern pipeline (`docs/pattern-pipeline/README.md`) is tested, and how
far to trust each test. Read this before reading a Tagging or whole-pipeline
Eval score as "Zeph's Patterns are right".

**Evals cost money.** Every run calls the real model. Before any run, remind
the owner and show the estimate: the Dashboard's New run page shows it before
Start run, and `make eval` prints it first. A full Tagging run (44 cases) is
estimated at about 308,000 tokens in and 40,000 out, about S$0.18 at the
prices of 24 Nov 2026.

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
the Observations kept are exactly the ones expected. The seed has 44 cases
over the three Pattern Types: clear, against, unclear, nothing to tag and
anyone-would-do-it.

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

### 3. The whole-pipeline Eval (later, issue 19)

Made-up Users with hidden true Patterns talk over several Conversations; the
Eval checks which Patterns became ready and how many were true. Target: at
least 70% of Ready Patterns true, starting with 5 Users.

- **Shows:** the pieces work together: tagging, scoring and the gate move
  the right Patterns and leave the rest.
- **Can't show:** truth. A model playing a User and a model tagging them
  tend to agree: the player writes the Pattern the way a model expects it to
  sound, and the tagger hears it. So this layer catches breakage, not
  whether Patterns are true or new to real people.

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

## How to run the Tagging Eval

Dashboard: Admin → Evals → New run, tick Tagging (or pick single cases),
read the estimate, Start run. Each result shows Expected, Kept by code and
Dropped by code. Terminal: `make eval EVALS=tagging`, or
`make eval CASES=conf-yes-to-sister-then-resents`. Cases are edited on Admin
→ Evals → Cases → Tagging; the seed is
`src/companion/seed/evals/cases/tagging.yaml`. How to correct the drafted
cases and add your own: `adding-tagging-cases.md`.
