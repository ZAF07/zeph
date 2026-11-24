# PRD: Tested Patterns: Zeph digs, tests what it finds, and shares what holds up

Status: ready-for-agent

## Problem Statement

Zeph is live, and it is still passive. From the User's side:

- It rarely asks anything that matters. With Admins allowing 5 Curiosities per Conversation and 7 Curiosity Check-ins a week, Zeph still brings up almost nothing meaningful. What it does ask are polite follow-ups ("how did the presentation go?") that aim at nothing.
- It doesn't remember what it is trying to learn about them. A question that gets a vague answer is simply closed; Zeph never comes back to it another way.
- What it says about who they are isn't tested. A Pattern is written freely by a model and confirmed by a single "yes", and people say yes to flattering reads and no to accurate ones that sting. A read like that can fit anyone, like a horoscope.
- A Pattern comes with nothing to check it against: not their own words, and nothing to try in their own life.
- A new User gets no sign for weeks that Zeph is paying attention to anything.

Behind this: a Curiosity can be dropped twice before it reaches the User (the Reply Plan is told to leave it out unless the moment is right, then the Reply gets it as an optional extra), it loses to every other question, and a model writes it with nothing to aim at. And nothing in the system separates what Zeph may wonder about from what it may claim.

For Admins: there is no way to say which Patterns Zeph may look for, how sure it must be before sharing one, or how hard it may dig; and no way to see what Zeph keeps noticing that it has no name for.

The product Zeph should be: "Zeph helps you see your own patterns. It turns everyday conversations and thought experiments into evidence-backed hypotheses about how you act in different situations, and you test them in your own life."

## Solution

Zeph becomes proactive in what it asks and strict in what it claims. The model reads and words; code decides (ADR-0024).

**Zeph digs.** Every **Curiosity** has an aim, and one the Reply Plan picks is part of the plan the Reply follows, not an optional extra (ADR-0026). Each **Need** says, as Admins set it, whether Curiosities are asked by default, tested lightly, asked only if they fit, or never, so banter stays banter. Zeph keeps an **Agenda**: a few **Explorations**, each its ongoing effort on one Pattern, remembering every try and what came back, so it can return days or weeks later a different way. **Thought Experiments**, written by Admins, tell look-alike Patterns apart and give a new User something to think about from the first Conversations.

**Zeph tests what it finds.** A human-written **Pattern Catalog** of **Pattern Types** says which Patterns Zeph may look for (ADR-0025). When a Conversation ends, a model tags **Observations**: the User's exact quote, who it was about, the situation, and which Pattern Type it speaks for or against. Code checks every quote word for word, works out a score, and alone moves each Pattern through its states, logging every move. Quotes are kept as User Memory after Message Retention deletes their messages (ADR-0027), and Users see and can delete every one.

**Zeph shares what holds up.** A Pattern is shared only when it is ready: seen across several Life Threads and Conversations, on clear evidence, tested against itself, with nothing safer to wait for. It comes as Zeph's view, with the User's own quotes and one **Prediction** to test in their own life. Zeph asks what would prove it wrong and follows up. Predictions that came true confirm it.

The **Read** stays free: Zeph still has an honest view of each situation from the first chat. Each User sets how direct it is.

It rolls out as three Features, each needing the one before: Pattern noticing (silent), Pattern exploring, Pattern sharing.

The full design is in `docs/pattern-pipeline/README.md`; every decision, starting number and the first fifteen Pattern Types are in `.scratch/pattern-pipeline/grill-decisions.md`; terms are in `CONTEXT.md`.

## User Stories

### Zeph asks things that matter

1. As a User, I want Zeph to ask me questions that are trying to learn something specific about me, so that our chats lead somewhere.
2. As a User, I want Zeph to ask about the exact moment I'm describing ("what did you do next?", "what were you hoping wouldn't happen?"), so that I look at what actually happened, not at a general idea of myself.
3. As a User, I want Zeph to come back later, in a different way, to something it asked that I didn't really answer, so that it doesn't give up on understanding me.
4. As a User, I want Zeph to remember what it already asked me and what I said, so that it never asks the same thing the same way twice.
5. As a User, I want Zeph to ask whether something would have gone differently with another person in my life, so that I notice where I act differently.
6. As a User, I want Zeph to give me a Thought Experiment now and then, so that I see how I'd choose in a situation I haven't faced.
7. As a User, I want Zeph to sometimes ask me to notice something over the coming week, so that I gather my own evidence.
8. As a User, I want a Thought Experiment to arrive as a Check-in sometimes, so that Zeph starts something worth thinking about.
9. As a User who is just chatting, I want Zeph to stay light and fun, and only now and then test the water with a deeper question, so that it never feels like an interview.
10. As a User who doesn't bite on a light opener, I want Zeph to drop it for the rest of the Conversation, so that I'm not pushed.
11. As a User who is venting or struggling, I want Zeph to ask me nothing of this kind, so that I'm heard first.
12. As a User, I want Zeph to leave a few replies between its questions, so that the chat still feels like a chat.
13. As a User who has brushed off a couple of questions in a row, I want Zeph to back off for a while, so that it respects my mood.
14. As a User, I want one real answer from me to bring Zeph's curiosity back, so that backing off isn't permanent.
15. As a User who asks Zeph to drop a topic, I want it never raised again unless I bring it up, so that my boundary holds.

### Being known from the start

16. As a new User, I want Zeph to ask me a few broad Thought Experiments in my first Conversations, so that it starts getting to know me straight away.
17. As a new User, I want Onboarding to stay as short as it is, so that I'm not given a quiz before my first chat.
18. As a new User, I want Zeph to have an honest view of what I tell it from the first chat, so that it is useful before it knows me well.
19. As a User, I want Zeph's questions to change as it gets to know me, from broad ones to ones about my real experiences, so that it doesn't keep treating me as a stranger.
20. As a User, I want to see the things I said that Zeph kept, so that I know it is paying attention long before it tells me a Pattern.

### Patterns that hold up

21. As a User, I want Zeph to tell me a Pattern only when it has seen it in several different parts of my life, so that it isn't just about one bad boss.
22. As a User, I want a Pattern to rest on more than one Conversation, so that it isn't just one bad evening.
23. As a User, I want ten complaints about the same person to count once, so that Zeph doesn't mistake repetition for evidence.
24. As a User, I want the same way of acting with different people in one part of my life to count for more, so that Zeph sees it isn't about one person.
25. As a User, I want Zeph not to count times when anyone would have acted as I did, so that a Pattern says something about me.
26. As a User, I want Zeph to look for times a Pattern didn't show up before telling me, so that it isn't only finding what it expects.
27. As a User, I want a Pattern narrowed when it shows up with some people and not others ("with seniors, not with friends"), so that it is exact about me.
28. As a User who shows two Patterns that look alike, I want Zeph to be able to see both, so that one doesn't hide the other.
29. As a User, I want Zeph to ask me when it can't tell why I did something, so that it doesn't guess which Pattern it was.
30. As a User going through grief, a breakup, a job loss or a crisis, I want Zeph not to draw or share Patterns from that time, so that I'm not judged at my worst.
31. As a User, I want some topics never explored or shared unless I raise them, so that painful ground is mine to open.
32. As a User, I want old evidence to count for less over time, so that Zeph's picture of me keeps up with who I am now.

### Being told a Pattern

33. As a User, I want a Pattern offered as Zeph's view, never as fact, so that I can think about it freely.
34. As a User, I want a Pattern to come with my own words from different parts of my life, so that I can see where it comes from.
35. As a User, I want one concrete thing to notice next time it comes up, so that I can test it in my own life.
36. As a User, I want Zeph to ask what would prove it wrong, so that I'm invited to push back honestly.
37. As a User, I want Zeph to ask later how the thing I was to notice went, so that the Pattern is checked against what really happened.
38. As a User, I want at most one new Pattern in a while, so that each has room to sink in.
39. As a User, I want a Pattern told at a moment that fits, and not while I'm struggling, so that it lands well.
40. As a User, I want a Pattern Zeph has been holding to reach me as a Check-in if no good moment comes, so that it isn't lost.
41. As a User, I want my agreeing to count, but not to settle it, so that Zeph isn't just telling me what I like to hear.
42. As a User who rejects a Pattern, I want Zeph never to offer it again unless I raise it, so that my no is respected.
43. As a User, I want to choose whether Zeph keeps quietly noting evidence for a Pattern I rejected, so that I decide how much of the hard parts I want found.
44. As a User, I want Zeph never to use clinical words or diagnose me, so that it stays a companion, not a clinician.

### My Dashboard

45. As a User, I want to see the Patterns Zeph has told me that are still being tested, with my quotes, the thing to notice and how it went, so that I can follow them.
46. As a User, I want to see my confirmed Patterns with their evidence, so that I can come back to what I've learned about myself.
47. As a User, I want to see Patterns I disagreed with, marked as such, so that I can delete them or stop Zeph gathering on them.
48. As a User, I want a Pattern I was told that didn't hold up shown as such, so that I can trust Zeph to say when it was wrong.
49. As a User, I want never to see a score or percentage on a Pattern, only words and the evidence, so that I'm not given false certainty.
50. As a User, I want not to see Patterns Zeph hasn't told me about, so that I'm not handed half-formed ideas about myself.
51. As a User, I want every quote Zeph kept listed with the day and a line on what was going on, with no Pattern named, so that I know exactly which of my words it holds.
52. As a User, I want to delete any kept quote, so that my words are mine to remove.
53. As a User, I want deleting a quote or a Pattern to change what Zeph thinks at once, so that a deleted thing is never used again.
54. As a User, I want to be told plainly that quotes kept as evidence stay after my messages are deleted, so that nothing is kept behind my back.
55. As a User, I want Delete My Data to remove every Pattern, quote and private note, hidden ones included, so that I can start fresh.
56. As a User with User Memory off, I want no new quotes kept and no Patterns changed, so that off means off.
57. As a User who already had Patterns, I want the ones I agreed with to stay, so that nothing I was told is taken back.
58. As an existing User, I want to be told what has changed before Zeph starts keeping quotes and looking for Patterns, so that I agree to it knowingly.

### How direct Zeph is

59. As a User, I want to set how direct Zeph is with its views (gentle, balanced, direct), so that it suits me.
60. As a User, I want to change that on the Dashboard or by telling Zeph in chat, so that it is easy.
61. As a User on the gentle setting, I want Zeph still to give its view when I ask, so that gentle never means empty.
62. As a User on the direct setting, I want Zeph to say its view sooner and more plainly, but never share an untested Pattern, so that direct doesn't mean careless.
63. As a User who is struggling, I want Zeph to be careful whatever my setting, so that safety comes first.

### Admins: the Pattern Catalog

64. As an Admin, I want to read every Pattern Type on the Dashboard with all its details and its status, so that I know what Zeph looks for.
65. As an Admin, I want a Pattern Type to be draft, approved or archived, so that only what I've approved can be shared.
66. As an Admin, I want a draft Pattern Type to gather evidence without ever being shared, so that I can watch it before approving it.
67. As an Admin, I want Pattern Types changed only through a reviewed change and a deploy, so that what Zeph may claim about people never shifts by accident.
68. As an Admin, I want every Observation to keep the catalog version it was tagged under, so that history can be scored again after a change.
69. As an Admin, I want a guide on how Pattern Types work and what each change does, so that I can manage the catalog safely.
70. As an Admin, I want fifteen starting Pattern Types across conflict, approval, control, achievement and relationships, so that Zeph has something to look for from the start.

### Admins: Thought Experiments

71. As an Admin, I want to add, edit, switch off and archive Thought Experiments on the Dashboard, so that I can improve them without a deploy.
72. As an Admin, I want each Thought Experiment to name the two Pattern Types it tells apart, how sensitive it is and whether it is a starter, so that Zeph uses it at the right time.
73. As an Admin, I want leading wording flagged when I save one, so that a question doesn't put the answer in the User's mouth.
74. As an Admin, I want a first set of Thought Experiments loaded for me, so that I'm not starting from nothing.
75. As an Admin, I want a guide on where to find material for Thought Experiments and how to write and manage them, so that I can add my own.

### Admins: tuning and seeing

76. As an Admin, I want each Need to say how Curiosities are treated while it is picked (ask by default, test the water, only if it fits, never), so that I control how forward Zeph is in each kind of moment.
77. As an Admin, I want every number in this (score bars, situations needed, fading, Agenda size, pace, backing off, weekly limits, follow-up waits, the new-User bars) to be a Platform Setting with a hint, so that I can tune Zeph without code.
78. As an Admin, I want to override those numbers in an Eval Variant, so that I can compare before making a change live.
79. As an Admin, I want three Features (Pattern noticing, Pattern exploring, Pattern sharing), each needing the one before, switchable for everyone or one User, so that I roll this out in stages.
80. As an Admin, I want to see how many Patterns a User has in each state and how well Zeph knows them, never their content, so that I can tell it is working without reading private things.
81. As an Admin, I want the Model Call Log to show, for each reply, how many Curiosities were offered and whether one was asked, so that I can see if Zeph is still passive.
82. As an Admin, I want the Model Call Log to show how many Observations were tagged and how many code dropped, so that I can see when the model is making things up.
83. As an Admin, I want every move of a Pattern between states kept with what caused it, so that any shared Pattern can be traced back.
84. As an Admin, I want a review list of what Zeph keeps noticing that fits no Pattern Type, as general descriptions with no User details and how many Users each appeared for, so that I know where the catalog should grow.
85. As an Admin, I want to mark each entry on that list as a new Pattern Type, folded into an existing one, or dropped, so that the list stays worked.
86. As an Admin, I want old unmatched evidence tagged again when a Pattern Type is added, so that nothing gathered is wasted.

### Admins: knowing it works

87. As an Admin, I want a Tagging Eval that checks the Observations tagged from made-up Conversations, including ambiguous ones, ones with nothing to tag and ones anyone would do, so that I can trust the step everything else rests on.
88. As an Admin, I want a whole-pipeline Eval with made-up Users who have hidden true Patterns, so that I can see which Patterns became ready and how many were true.
89. As an Admin, I want a guide saying what these Evals can and can't show and what must be done later, so that I don't trust them for more than they prove.

## Implementation Decisions

### Shape

- Patterns are evolved, not replaced: one store of what Zeph suspects about a User. ADR-0024 replaces ADR-0020.
- The model reads and words; code decides. Scoring, the ready gate, state moves, ranking the Agenda and writing aimed Curiosities are pure functions in the core with no model call. Prompts hold no numbers.
- Everything follows ports and adapters (ADR-0003), plain core code with no graph framework (ADR-0009), and one job per model call (ADR-0021).

### Curiosities (slice 1, no catalog needed)

- Every Curiosity has an aim: an Exploration's need, a Prediction or commitment to follow up, a look-back, or a guess to check. One with no aim is never made.
- Each Need gains a field for how Curiosities are treated while it is picked: ask by default, test the water, only if it fits, never. Being heard starts as never; Just chatting starts as test the water.
- Ask by default: the Reply Plan must bring one up or give a reason. Test the water: one light opener; if the User doesn't engage, none for the rest of the Conversation.
- A Curiosity the Reply Plan picks moves from the Reply's optional extras to the Reply Plan's level in the priority order.
- Pace, all Admin-set: a fewest replies between two Curiosities; a separate cap on follow-ups to a story the User is telling now (these don't use the Curiosity budget); after a number of brush-offs in a row, none for the rest of the Conversation and the spacing doubled for a time, ended by one engaged answer.
- The Model Call Log's Reply Plan shape records Curiosities offered and asked.

### Pattern Catalog

- Pattern Types are YAML in the repo, loaded into the database on deploy, read-only on the Dashboard (ADR-0025). Each has a stable ID, a version, one of five areas, a definition, its if / then / function, signs (each with a strength and the part it shows), signs against, look-alikes with what tells them apart (including what anyone would do), exclusions with whether evidence is ignored or counted but not shared, approved wording, Prediction wording, its own numbers, and a status with who approved it and when.
- The first fifteen are listed in the decisions file; all start as draft.

### Observations and tagging

- A new Conversation-end step after Life Threads and before Pattern keeping. It is given the Conversation, the Threads touched and the whole catalog. Own prompt, model and thinking switch as Platform Settings.
- An Observation holds: User, Pattern (and Pattern Type with its catalog version), the sign matched, for or against, the quote, the context line, the day, the Life Thread if any, who it is about, relationship, power, setting, stance, the kind of evidence, whether it is unclear (and the second Pattern Type), and whether it is situational.
- Code keeps only Observations whose Pattern Type and sign exist, whose quote is word for word in the User's own texts of that Conversation, and whose tags come from the fixed lists. Drops are counted in the Model Call Log.
- The step also flags when one of a Pattern Type's exclusions applies to the User now, from their open Life Threads and recent Day Summaries.
- Observations are User Memory and outlive Message Retention (ADR-0027). Deleting one scores its Pattern again. Deleting a Life Thread removes its Observations.

### Scoring, states and the log

- Score: each Observation's weight is its sign's strength times its kind of evidence, reduced when unclear, zero when situational, negative when against, fading by a half-life at read time. Within a Life Thread only the strongest Observation per person counts, up to a cap of people. A situation is one Life Thread; with no Thread, the same person and setting.
- The score is computed from Observations, never stored as the source of truth; a snapshot may be cached for the Dashboard.
- Seven states: noticed, suspected, ready, shared, confirmed, contested, closed. Every move is a pure function of the evidence and is saved in an append-only log with its cause. Moves can go back.
- Reactions: the model reads agreed / pushed back / brushed off; code counts agreement as a weak sign for, rejection as contested plus a weak sign against, a Prediction that came true or didn't as a strong sign for or against.
- A contested Pattern keeps gathering only while the User's own switch allows.
- Unmatched Patterns are written by the existing Pattern keeping step, which no longer starts, confirms or closes catalog Patterns. They are never ready.
- Existing Patterns are migrated in place: confirmed stay confirmed and visible, suspected become unmatched, closed stay closed; a one-off pass matches each to a Pattern Type where one fits. No User data is lost.

### Agenda, Explorations, Thought Experiments, Familiarity

- An Exploration belongs to one Pattern and holds its open needs (unclear story, missing part of life, counter-test), each try (Curiosity, when, outcome: useful, vague, brushed off), and what to try next and not before when.
- After scoring, code keeps the Agenda at the Admin-set size, ranks it, and writes the next aimed Curiosity for each Exploration, least pushy way first. An Exploration is never worked on two Conversations in a row, waits after a try with nothing, rests after an Admin-set number of tries and wakes on new evidence.
- The next Thought Experiment targets the look-alike pair with the most unclear evidence.
- Thought Experiments are Admin-managed data with a Dashboard page, seeded once, archived never deleted. A check on save flags leading wording. Asked as Curiosities in chat or through the existing Curiosity Check-in Kind and its weekly limit. An answer becomes an Observation of the "what if" kind.
- Familiarity (new, getting to know, knows well) is worked out by code from counts at each Conversation end. The Reply Plan is given it and the Agenda, with earlier tries, on every reply.
- Get curious stays the in-the-moment Move and is given the Agenda's open needs to aim with.

### Ready gate and sharing

- The ten checks in the pipeline doc, in code. One model call argues for a better explanation and can only block.
- The Reply Plan is offered only ready Patterns to share; others in mind are marked not to be said. The Read may think with any of them.
- A shared Pattern is written from its Pattern Type's approved wording, two or three quotes from different Life Threads, and one Prediction. A small check after the Reply says whether it was shared; only then does it count toward the weekly limit and move to shared.
- A ready Pattern not shared within an Admin-set time goes out as a Check-in.
- The Prediction gets a follow-up Curiosity after an Admin-set wait, dropped after a longer one.
- The Memories page's Patterns tab shows shared, confirmed, contested and once-shared closed Patterns, with words and evidence and no number. A new list shows every kept quote with no Pattern named.

### Around it

- Three Features: Pattern noticing, Pattern exploring, Pattern sharing; each works only when the one before does; all off to start.
- A directness setting per User (gentle, balanced, direct), changeable on the Dashboard and as a Chat Setting Change, given to the Reply Plan; ignored while the User is struggling; never an input to the gate.
- An Admin page lists unmatched Patterns grouped as general descriptions with no User details and a count of Users; each can be marked new Pattern Type, folded or dropped.
- Every new Platform Setting has a hint and can be overridden in an Eval Variant. Starting values are in the decisions file.
- New Copy slots for the Patterns tab, the kept-quotes list, the retention note and the notice to existing Users.
- Delete My Data and Account Deletion remove Observations, Patterns in every state, Explorations and the log.
- Three guides are written with the slice they describe: the Pattern Catalog, Thought Experiments, and the Pattern Evals.

### Build order

Six slices, each usable by itself: (1) Curiosity standing; (2) catalog, tagging, Observations, Tagging Eval, kept-quotes list; (3) scoring, states, log, unmatched, migration; (4) Agenda, Explorations, Thought Experiments, Familiarity; (5) ready gate, sharing, Predictions, Patterns tab; (6) unmatched review page, directness, remaining guides.

## Testing Decisions

A good test here checks what a User or Admin would see or what is saved, never how a step is built inside: a text arrives, the Conversation ends, and the test looks at what was sent, what the Dashboard API returns and what the model was given.

**Seam 1, the main one: the whole backend through its HTTP edge.** Texts go in through the Telegram webhook and Dashboard calls through the API, with the scripted chat model, fake chat channel, fake clock and fake scheduler at the ports and a real Postgres. Tests script the model's answers (a tagging answer, a Reply Plan answer), move the clock to end a Conversation, and assert on what was sent, what the API returns and what the next model call was given. This is how Patterns, Curiosities, Life Threads and Check-ins are tested today, and it needs no new seam. Scripted-answer helpers are added for the tagging step, as exist for the Understanding and the Reply Plan.

**Seam 2: the pure decision functions.** Scoring, counting situations, the ready checks, state moves, ranking the Agenda, pace and backing off, and Familiarity are pure functions tested directly with plain values, with no database or model. Prior art: the message wait rule and the Check-in decision.

**Evals, separate and on demand (they cost money):**

- A Tagging Eval as a new Eval kind in the existing Eval runner: a case is a made-up Conversation and the Observations expected. About 40 starting cases, including ambiguous ones (must come back unclear), nothing to tag (must come back empty) and what anyone would do.
- A whole-pipeline Eval later: made-up Users with hidden true Patterns over several Conversations; target at least 70% of ready Patterns true; 5 Users to start.
- Their limits are written in the Pattern Evals guide: a model playing a User and a model tagging them tend to agree, so the whole-pipeline Eval catches breakage, not truth.

**Also tested:** each migration keeps existing Patterns and their evidence; the catalog loader refuses a malformed Pattern Type; Dashboard pages with Vitest and React Testing Library, and built against the design reference with the pixel test (ADR-0018); every acceptance criterion gets a check in the running app before it is ticked.

## Out of Scope

- A model suggesting Pattern Types from the unmatched review list and the backend saving them into the YAML, and Pattern Types in a git submodule. Detailed in the decisions file for its own PRD.
- Editing Pattern Types on the Dashboard (draft, Eval, Make Live).
- Helping Users work on a difficult Pattern.
- Confirming Patterns on the Dashboard.
- The quality of banter and humour (the Persona's voice and the Just chatting Need).
- Calling the score a probability, learned weights, and a second rater with 200 labelled Observations.
- A psychologist's review of the catalog: needed before this is opened widely, not built here.
- Voice, other languages, anything clinical.

## Further Notes

- Production has a real User. Migrations must keep their data, and they must be told what changed before Pattern noticing starts for them.
- Slice 1 is the quick win against "Zeph is passive" and depends on nothing else.
- The tagging step is the foundation: its Eval is built with it, before scoring is trusted.
- Evals cost money: every run shows its estimate first, and the owner is reminded before any run.
- With fifteen Pattern Types most of what Zeph notices will be unmatched at first, so the review list sets how fast Zeph can share more.
- Source design: "Zeph insight pipeline" and its Pattern Catalog doc, linked from the decisions file.
