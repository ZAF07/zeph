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
(situational) or not, and optionally the Conditions it must hold (audience,
stakes, state going in: a value, or "must be empty"; one not stated isn't
checked). The real tagging step runs on it with the whole
Pattern Catalog, code checks what it wrote, and the case passes only when
the Observations kept are exactly the ones expected. The seed has 68 cases:
44 over the first three Pattern Types (clear, against, unclear, nothing to
tag and anyone-would-do-it), and one for and one against each of the twelve
added later. Ten more (`cond-…`, issue 41) are about Conditions: one said
so tagged, none said so all empty, a feeling afterwards that is not a state
going in, one person inside a group, and high stakes said plainly.

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
    other than "anyone would" and the Conditions a case states are filled
    in (relationship, power, setting, stance and kind of evidence are only
    checked against their lists).
  - "Anyone would" for ACH.WORTH.PERF and CTRL.UNCERT.PLAN: their "anyone
    would" (high stakes, a real crisis) can't be written as tags, so code
    never marks theirs situational. Those cases expect the step to say
    nothing, or a sign against.

#### Conditions: first results (26 Nov 2026)

The ten `cond-` cases, one try each.

| Run | Tagging model | Passed | Cost |
|---|---|---|---|
| `7f09461a` | deepseek-v4.1-flash (live), first prompt | 7 of 10 | S$0.078 (estimate S$0.04) |
| `bd350ed4` A | deepseek-v4.1-flash (live) | 9 of 10 | about S$0.06 |
| `bd350ed4` B | claude-opus-5.5 | 9 of 10 | about S$0.81 |
| `bd350ed4` C | claude-haiku-5.5 | 10 of 10 | about S$0.02 |

- **State going in** was right in all 40 results: tagged when said, empty for a feeling afterwards.
- **First run:** the model filled audience "one-to-one" whenever the story had one other person, and stakes "low" or "high" unsaid, in 4 cases. The prompt now says not to. Two drafts also drew a look-alike (APPR.GIVE.NEEDED) and were rewritten.
- **Second run:** no Condition was wrong on any of the three models. The two fails were not about Conditions: flash wrote "hers" in a context line (`cond-state-worn-out-before-call`), and Opus called `cond-high-stakes-visa-interview` unclear between ACH.WORTH.PERF and CTRL.UNCERT.PLAN.
- The run's estimate (S$0.22) priced every Variant at the live model; the real total was about S$0.90.
- Ten cases, one try: a first look, not a score. The owner still corrects the drafts.

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
when every ready Pattern is a true one, at least one of its true Patterns
became ready, and no Conversation-end step failed. A User with no true
Pattern passes with nothing ready. Target for a run: at least 70% of
ready Patterns true. The seed has 6 made-up Users: one true Pattern with a
"not with my partner", two true look-alikes, none, one true whose look-alike
is not, one true beside a single story of its look-alike, and one true who
then asks Zeph what it has noticed, so the Pattern can be shared.

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
  - That 70% means anything for real Users. Six scripted Users give a
    handful of ready Patterns, so one more or one fewer moves the share a
    lot. Read each case, not only the share.
  - Every missed Pattern as a failure. A case fails when none of its true
    Patterns became ready, so a dead pipeline is no longer all passes. A
    case with two true Patterns still passes when it finds one: read "true
    Patterns found".
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
    fading and the wait before a Check-in shares are never reached. Sharing
    in chat is reached: `asks-what-zeph-noticed` asks for it.
  - A steady result. Zeph's replies and the tagging vary from run to run,
    so the same case can find a Pattern one day and miss it the next. Use
    Repeats before trusting a change.

#### How to read a Whole-pipeline result (changed 25 Nov 2026, issue 32)

- **Pass** now means three things: every ready or shared Pattern is a true
  one, at least one true Pattern became ready (when the User has any), and
  every Conversation-end step ran.
- **Fail, "true Patterns found: 0 of N became ready":** the User has true
  Patterns and none became ready. Either the script doesn't give enough
  (look at "True Patterns missed" and its "Stopped by") or the pipeline is
  broken. Before, this was a Pass.
- **Fail, "Conversation-end step failed":** a step such as scoring, the
  ready gate or the Portrait failed and was skipped, as the live app does.
  The line says after which Conversation and what failed ("after
  Conversation 2: Could not score Patterns: ..."). Before, this was only
  in the log. It is read from the failures the app logs while the
  Conversation ends, so anything else that fails in that scheduled work
  shows here too.
- On the Dashboard both reasons are the first lines of a failed case's
  "What happened", under "Why it failed". The terminal report prints them
  as FAIL lines.
- A User with no true Pattern (`ordinary-fortnight`) still passes when
  nothing becomes ready.

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
should.

## Second Whole-pipeline results (25 Nov 2026, issue 32)

Each case was run alone, once, on the live settings:

| Case | Result | Tokens in / out | Cost |
|---|---|---|---|
| `goes-quiet-and-says-fine` | Pass. CONF.WITHDRAW.HURT ready; APPR.HIDE.BURDEN suspected, stopped by situations | 391,000 / 175,000 | S$0.42 |
| `never-arrives` | Pass. ACH.GOAL.MOVE ready, then shared in chat; the single look-alike story didn't become ready | 338,000 / 147,000 | S$0.36 |
| `cannot-stand-waiting`, as first drafted | Fail. CTRL.UNCERT.PLAN suspected, stopped by score | 307,000 / 112,000 | S$0.29 |
| `cannot-stand-waiting`, script corrected | Pass. CTRL.UNCERT.PLAN ready, then shared in chat | 300,000 / 143,000 | S$0.33 |
| `asks-what-zeph-noticed` (new), first script | Fail. CONF.AVOID.BELONG suspected, stopped by counter-test | 406,000 / 173,000 | S$0.42 |
| `asks-what-zeph-noticed`, second script | Fail. Suspected, stopped by situations | 380,000 / 149,000 | S$0.37 |
| `asks-what-zeph-noticed`, third script | Pass. CONF.AVOID.BELONG ready after 5 Conversations, shared in chat in the 6th, when asked | 388,000 / 188,000 | S$0.44 |

Seven case runs, S$2.63 in all. Across the five seeded cases with a true
Pattern, each as last run (these four and `folds-with-sister-and-friends`
from the first results): 5 of 5 ready Patterns were true, and 5 of 6 true
Patterns were found. No look-alike
became ready. Three Patterns were shared in real runs. Each case was run
once, so this is not a steady figure: use Repeats.

What the failed runs taught about writing a script (also in the seed
file's header):

- Tell the strongest sign as a story ("last night I…"), not an opinion. An
  opinion counts for less and the Pattern stops at "score".
- Keep the "it doesn't happen with…" story to one text that names the
  person and who they are ("my husband Idris"). A second line that only
  compares ("it's only with mum and friends that I cave") was tagged as
  evidence against with no person; then nothing is narrowed and the
  Pattern stops at "counter-test".
- A story about a parent or a boss can be tagged "above". For Pattern
  Types whose "anyone would" is "people in charge" it then counts for
  nothing and the Pattern stops at "situations". Use people on the same
  footing.

The findings are in
`.scratch/pattern-pipeline/issues/20-findings-for-the-owner.md`, section 32.

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
minutes (25 Nov 2026). The longer ones (16 to 20 texts) used 300,000 to
390,000 in and 110,000 to 190,000 out, S$0.29 to S$0.44, 12 to 21 minutes
each. Until a case has run once its estimate is a rough 300,000 tokens in
and 110,000 out, which was low for most of them. The 6 cases together pass the Eval run
token limit (1,000,000 to start; Admin → Evals → Model Prices), and the run
then stops between Conversations, so raise the limit first or run one case.

Dashboard: Admin → Evals → New run, tick Whole pipeline (or open it and pick
single cases), read the estimate, Start run. Each result shows "Became ready
or shared" and "True Patterns missed"; a failed one's "What happened" starts
with "Why it failed". Add a Variant to try another gate
number or prompt on the same Users. Terminal: `make eval
EVALS=whole_pipeline`, or `make eval CASES=ordinary-fortnight`; a plain
`make eval` leaves this Eval out. Cases are edited on Admin → Evals → Cases
→ Whole pipeline; the seed is
`src/companion/seed/evals/cases/whole_pipeline.yaml`, drafted by Claude for
the owner to correct.

## The case for "what patterns do you see in me?" (25 Nov 2026, issue 39)

`asked-for-patterns-nothing-ready`, an Understanding case. The made-up User
has a suspected Pattern (two clear stories, Mei and Jo) and nothing ready
or told, and asks "what patterns do you see in me? tell me one". The gate
wins when they ask (ADR-0030), so the reply must say Zeph is still getting
to know them and state no pattern. The Judge rule is
`says_no_pattern_when_asked`, drafted by Claude for the owner to correct.

- **What it shows:** whether the Reply Plan model reads the ask
  (`asked_for_patterns` in its form, seen in the Reply Plan step of the
  case result) and whether the reply then keeps to the fixed section code
  gives it.
- **What it can't show:** the two other branches (a ready Pattern shared
  when asked, a told Pattern recalled). Those are code, with tests in
  `tests/test_told_patterns_in_replies.py`, and the first is reached by
  the Whole-pipeline case `asks-what-zeph-noticed`.
- **Run it:** `make eval CASES=asked-for-patterns-nothing-ready`, about a
  cent. Use Repeats before trusting it: one Message, one run.

First results (25 Nov 2026, each try the same Message):

| Reply Plan and Reply model | Passed | Cost |
|---|---|---|
| deepseek-v4.1-flash (live), runs `b3e02c71`, `eb3cef1b`, `0a3eed92` | 3 of 3 | S$0.024 |
| deepseek-v4-pro, run `898e711d` A | 1 of 3 | about S$0.13 |
| claude-fable-5.2, run `898e711d` B | 1 of 3 | about S$0.71 |
| claude-opus-5.5, run `898e711d` C | 3 of 3 | about S$0.33 |

In all 12 tries the Reply Plan read the ask and the reply said it had no
pattern yet. The 4 fails added a view of the asking itself ("you'd rather
hear something true than something nice"), which the Judge read as a claim
about them; the made-up User had told no story in that Conversation. The
fixed section now says to give no view when no situation was told (not run
again). The three-model run was estimated at S$0.07 and cost about S$1.2:
the estimate doesn't price a Variant's dearer model.

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
