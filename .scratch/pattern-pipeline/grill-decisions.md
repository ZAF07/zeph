# Pattern pipeline: decisions from the grill

Source: `/Users/zaffere/projects/ai-chat-companion-assets/Zeph insight pipeline.md` and its Pattern Catalog doc (https://claude.ai/artifact/D2yWvHc2wztGNyjB5cjRnh). Started 24 Nov 2026. Not yet in `CONTEXT.md` or ADRs.

## Purpose

"Zeph helps you see your own patterns. It turns everyday conversations and thought experiments into evidence-backed hypotheses about how you act in different situations, and you test them in your own life."

Tagline: "Zeph turns your conversations into testable insights about how you really work."

Zeph must be proactive and opinionated, not passive: it digs, asks and forms Patterns; code gates what it claims, never how curious it is. Balance: it can still just banter and be fun.

## Decided

1. **Evolve Patterns**, no separate pipeline. Replaces ADR-0020. The live User's Patterns must survive the migration.
2. **Names.** Keep Pattern (Hypothesis goes on its avoid list). New: Pattern Catalog (codebook), Pattern Type (one entry), Observation (one quoted piece of evidence), Thought Experiment, Exploration, Agenda. Session stays Conversation.
3. **Pattern Type shape** follows CAPS: situation → inner processing → behaviour (if / then / function). Frameworks fill it. Each indicator has a `caps_unit` tag.
4. **Where things live.** Pattern Types (with Thought Experiments and per-type numbers) in git as YAML, loaded on deploy, read-only for Admins: an exception to ADR-0004, needs its own ADR. Global numbers are Platform Settings with hints, overridable in Eval Variants. Prompts stay Admin-editable and hold no numbers.
5. **User reactions.** The model reads the reaction; code decides what it means. Agreement is supporting evidence that adds up; code confirms. Rejection: Zeph stops offering it (unless the User raises it) and keeps gathering silently; the User has a switch for the silent gathering, on by default.
6. **The Read stays free** (a view of this situation). **Sharing a Pattern is gated by code**: the Reply Plan is offered only ready Patterns; others are in mind but marked not to be said. A check after the reply says whether one was shared.
7. **Directness setting** for Users (gentle / balanced / direct): how and how soon Zeph says its Read. Never touches the Pattern gate; ignored while struggling. Its own issue.
8. **Observations keep the exact quote past Message Retention**, as User Memory: visible, deletable (re-scores the Pattern), removed by Delete My Data. Each has the quote (checked by code), a context line by the model (shown apart as Zeph's note), day, Life Thread, situation tags.
9. **Independent situation = Life Thread** (fallback with no Thread: same person and setting). Within a Thread, different people add weight: strongest Observation per person, capped (Admin-set, start 3). The gate still needs 3 Threads.
10. **Situation tags**, closed lists: relationship (partner, family, friend, acquaintance, colleague, stranger) and power (above, equal, below), plus the doc's setting and stance. Store all; compare on coarse ones first.
11. **Score now, probability later.** Same maths as the doc (weights added, fading). Gate on counts plus score. Users see words and evidence, never a percentage. Becomes a probability once prediction outcomes show it is calibrated.
12. **Look-alikes compete per Observation**, not per person. An Observation the model can't place is "unclear" and counts little toward both. The gate needs enough clear situations; no margin rule. The next question targets the pair with the most unclear evidence.
13. **Curiosities are refactored, not replaced.** One module, one budget.
    - Every Curiosity has an aim: an Exploration's need, a commitment follow-up or a guess to check. None without an aim.
    - Code writes the ones from the Agenda and ranks all; the model only words them. Three sorts of need: unclear story, missing part of life, counter-test.
    - Each Need has an Admin-set field for Curiosities: ask by default, test the water, only if it fits, never. Just chatting: test the water (sparingly, light opener, back off if the User doesn't bite).
    - Once the Reply Plan picks one it is part of the plan (level 3), not an optional extra (level 6).
    - Get curious stays the in-the-moment Move, aimed by the Agenda.
    - Why today's are passive (found 24 Nov): dropped twice (Reply Plan, then level 6), lose every tie, no aim. Not the budget: live limits are 5 per Conversation, 15 waiting, 7 Check-ins a week.
14. **Exploration and Agenda.** An Exploration is Zeph's ongoing effort on one Pattern: what it is trying to learn, each try (which Curiosity, when, what came back), what to try next and not before when. A try that gets nothing useful keeps the need open; Zeph returns later a different way (story follow-up → "would it differ with…" → Thought Experiment → "this week, notice when…"), seeing the earlier tries. The Agenda is the User's active Explorations; how many at once is Admin-set (start 3). The Reply Plan sees it every reply.

15. **Thought Experiments are Dashboard-editable now**, like Moves: wording, the two Pattern Types it tells apart, sensitivity, on/off. Archived, never deleted. First set from a seed file. A check on save flags leading wording. Pattern Types stay in git for now; Dashboard editing (draft → Eval → Make Live, every version kept) comes once the catalog is stable.
16. **A Pattern is ready** when code finds all true: (1) at least 3 situations (Life Threads); (2) across at least 2 Conversations; (3) resting on clear Observations; (4) score past the bar; (5) tested against itself: at least one counter-test asked and answered, evidence against under a bar; a counter-test showing it doesn't happen there narrows the Pattern ("with seniors, not friends"); (6) situational Observations (tags match the Pattern Type's "anyone would do this" description) carry no weight; (7) every quote checked word for word; (8) one model call argues the other side and can only block; (9) safe: no Pattern Type exclusion applies (flagged by the tagging step from open Life Threads and recent Day Summaries; the catalog says whether evidence is ignored or counted but not shared), no recent Safeguard Event or struggling, not a never-topic unless the User raised it; (10) not rejected by the User. Numbers are Admin-set.
17. **Sharing a ready Pattern.** In chat at a moment the Reply Plan picks; as a Check-in if none comes within an Admin-set number of days. Always three parts: the Pattern in warm words as Zeph's view, 2 or 3 of the User's quotes from different parts of their life, and one Prediction to test ("next time…, notice whether…"). Zeph asks what would prove it wrong. A follow-up Curiosity aimed at the Prediction comes after an Admin-set wait (start 7–14 days); 2 Predictions that came true confirm it. New Patterns shared per week is Admin-set (start 1). Wording from the catalog's approved phrasing, fitted by the model.

18. **Seven Pattern states, moved only by code, each move saved in an append-only log with its cause.** Noticed (first Observation; record only) → Suspected (at least 2 situations and a low score bar; may get an Exploration) → Ready (all ten checks) → Shared (with a Prediction) → Confirmed (2 Predictions came true, or strong evidence after sharing). Contested (User rejected; never offered; gathers silently if their switch allows). Closed (score under a floor; reason kept). Can move backwards (Ready → Suspected). "Investigating" is having an Exploration; "dormant" is fading. Today's suspected, confirmed and closed map straight across.
19. **What Users see.** Only Patterns Zeph has told them about: Shared ("testing", with quotes, the Prediction and how it went), Confirmed, Contested ("you disagreed"; can delete or turn silent gathering off), and Closed only if it was ever shared ("didn't hold up"). Hidden: Noticed, Suspected, Ready, the Agenda, Explorations, scores. Exception for privacy: a plain list "Things you said that Zeph kept" shows every kept quote with its context line and day, no Pattern label, deletable (re-scores the Pattern). Admins see counts only.
20. **Unmatched Patterns.** The model may still notice freely; what recurs across Life Threads and fits no Pattern Type is kept as an unmatched Pattern. Never shared as a Pattern (the gate can't test it), hidden, but the Read may think with it. When a Pattern Type is added, old unmatched evidence is re-tagged against it. The live User's Patterns: confirmed stay visible and confirmed; suspected become unmatched; a one-off pass matches each to a Pattern Type where one fits.
21. **Unmatched review list (in this work).** An Admin page listing what keeps turning up unmatched: a general description with no User details, and how many Users it appeared for. No quotes, no names. The Admin marks each: new Pattern Type, folded into an existing one, or dropped. Writing the YAML is manual.

22. **Tagging step.** At Conversation end, after Life Threads and before Patterns. Reads the Conversation, the Threads touched and the whole catalog (no search step until the catalog is several times bigger). Per Observation it writes: Pattern Type (one, or two = unclear) and the sign matched; for or against; the exact quote; who it's about and the situation tags; the kind of evidence (real story, reported habit, answer to a "what if", own opinion of themselves; weighted in that order); the context line. Code drops any whose Pattern Type or sign isn't in the catalog, whose quote isn't word for word in the User's own texts, or whose tags aren't from the closed lists; drops are counted in the Model Call Log. Own prompt, model, thinking switch and Eval. Unmatched noticing stays in the Pattern keeping step (ADR-0021).
23. **Review status and rollout.** A Pattern Type is draft, approved or archived, with who approved it and when; only approved ones may become Ready, drafts gather silently. The owner approves for now (no reviewer yet). Three Features on the Features page, each needing the one before, all off to start, per User or for everyone: Pattern noticing (silent tagging and scoring), Pattern exploring (Agenda, aimed Curiosities, Thought Experiments), Pattern sharing (approved Pattern Types shared with Predictions). Numbers live on Platform settings. Existing Users are told plainly what changed before noticing starts for them.
24. **Testing, three layers.** (1) Scoring, the gate and state moves are pure code: ordinary tests, free, every change. (2) A Tagging Eval, built first: a case is a made-up Conversation plus the Observations expected, including ambiguous cases (must come back unclear), nothing-to-tag cases and "anyone would do this" cases; about 40 to start, drafted by Claude and corrected by the owner (the one rater), growing toward the doc's 200. (3) A whole-pipeline Eval later: made-up Users with hidden true Patterns over several Conversations, target at least 70% of Ready Patterns true, starting with 5 Users. Limits: a model playing the User and a model tagging them tend to agree, so layer 3 catches breakage, not truth; whether Patterns are true and new to real people comes only from real Prediction outcomes and reactions. Evals cost money; every run shows its estimate first.

25. **Cold start.** Onboarding stays as it is. Admins mark some Thought Experiments "starter" (broad, one per area); Zeph offers them in a new User's first Conversations under the usual Need rules, how many and over how many days Admin-set. Answers are weak evidence: enough for Noticed and to point the Agenda, never enough for Ready. Needs Pattern exploring on.
26. **Familiarity**: how well Zeph knows a User, worked out by code from counts (Conversations, Life Threads, Observations from real stories, Pattern states; bars Admin-set), recomputed at each Conversation end. New (starter Thought Experiments, broad Get curious) → Getting to know (the Agenda takes over, questions aimed at real experiences, starter questions stop) → Knows well (at least one Pattern Shared or Confirmed: Prediction follow-ups, narrowing Patterns). The Reply Plan is told it in one line every reply; Admins see it per User. Separate from the rollout Features.
27. **Build order, six slices.** (1) Curiosity standing fix: per-Need field, picked Curiosity is part of the plan; no catalog needed. (2) Catalog, tagging, Observations, Tagging Eval, "Things you said that Zeph kept"; Feature Pattern noticing. (3) Scoring, states, log, unmatched Patterns, moving the live User's Patterns across. (4) Agenda, Explorations, Thought Experiments admin page and first set, Familiarity, starter questions; Feature Pattern exploring. (5) Ready gate, sharing, Predictions, new Patterns tab; Feature Pattern sharing. (6) Unmatched review page, directness setting, remaining docs. Each guide is written with the slice it describes.

28. **Pace and backing off**, all Admin-set, all in code. Fewest replies between two Curiosities (start 3). Follow-ups on a story the User is telling right now don't use the Curiosity budget; own cap per Conversation (start 3). After brush-offs in a row (start 2): none for the rest of the Conversation and the gap doubles for a while (start 3 days); one engaged answer resets it; "drop it" stays final for that topic. Per Exploration: never two Conversations in a row; wait after a try that got nothing (start 3 days), then a different way; rests after tries with nothing (start 4), woken by new evidence; Thought Experiments per Pattern per week (start 1). Thought Experiment Check-ins use the existing weekly Curiosity Check-in limit.
29. **Starting values** (first guesses, tuned by Evals and real use). Sign weight weak / moderate / strong: 0.3 / 0.7 / 1.4. Kind of evidence, real story / reported habit / "what if" answer / own opinion: ×1 / ×0.7 / ×0.4 / ×0.3. Unclear: ×0.25 toward each. User agrees / rejects: one weak sign for / against. Prediction came true / didn't: one strong sign for / against. Half-life 75 days. People per Life Thread 3. Suspected: 2 situations, score 1.0. Ready: 3 situations, 2 Conversations, score 3.0, evidence against under 1.0. Closed under −1.5. Predictions to confirm 2. New Patterns shared per week 1. Ready waits 5 days for a moment, then a Check-in. Prediction follow-up after 7 days, dropped after 21. No sharing for 14 days after a Safeguard Event. Agenda 3. Starter Thought Experiments: 4 over the first 14 days, at most 1 per Conversation. New → Getting to know: 5 Conversations and 3 Life Threads, or a first Suspected Pattern.
30. **First fifteen Pattern Types**, five areas, all draft, each written in full in slice 2 for the owner to approve.
    - Conflict: (1, drafted) softens or hides their view with people who matter → to protect closeness; (2) hits back or explains at once when criticised → to protect how they see themselves; (3) goes quiet and pulls away when hurt → to avoid showing they need someone.
    - Approval: (4) says yes and over-gives when asked for help → to feel needed; (5) asks others to confirm a choice already made → to quiet the fear of having got it wrong; (6) shows "I'm fine" and hides what's hard → to avoid being a burden.
    - Control: (7, drafted) plans, checks and takes over when the outcome is unknown → to ease not knowing; (8) does it all themselves rather than lean on others → to avoid being let down; (9) keeps options open and delays committing → to protect their freedom.
    - Achievement: (10, drafted) judges themselves, not the work, after falling short → to protect a sense of worth; (11) when something grabs them, everything else goes quiet → to stay in the pull of it; (12) moves the goal as soon as they reach it → so "enough" never has to be faced.
    - Relationships: (13) reads silence or distance as something wrong and reaches out to check → to feel secure in the bond; (14) pulls back when someone gets closer or needs more of them → to protect their independence; (15) takes on other people's moods as theirs to fix → to keep things calm and feel safe. Longest exclusion lists; abuse stays a never-topic for the Safeguard.
    - Look-alikes: 13 vs 5 (the bond, not being wrong), 13 vs 7 (only about people), 14 vs 3 (when things are close, not after a hurt), 14 vs 9 (closeness, not choices), 15 vs 4 (steps in unasked), 15 vs 1 (acts to fix, not stays quiet).

## Parked: catalog suggestions by a model (own PRD)

Discussed 24 Nov 2026, deliberately left out of this work as too big.

- On the unmatched review page, a button sends the review list plus every Pattern Type with its description and definition to a model. Its prompt is Admin-editable.
- The model returns recommendations (new Pattern Type, fold into an existing one, drop). The Admin selects each or all.
- The backend saves the selected ones into the Pattern Type YAML automatically.
- Pattern Types could live in a git submodule, since they are git-tracked.
- To solve in that PRD: a running server can't simply write to git (open a pull request, or push to the submodule's repo with its own credentials; see ADR-0023 on deploys); a suggested Pattern Type still needs signs against, look-alikes, exclusions and a reviewer's sign-off, so it should be saved as a draft, not live.

## Parked

- Helping Users work on a difficult Pattern (ways to help themselves).
- Confirming Patterns on the Dashboard.
- Banter and humour quality (Persona voice, Just chatting Need): separate from this work.

## To deliver

- Admin guide: `docs/pattern-catalog/README.md` (what the catalog is, how to change a Pattern Type, what each change does).
- Admin guide: `docs/thought-experiments/README.md` (how they work, how to edit, what an edit changes).
- Evals guide: `docs/pattern-evals/README.md` (the three layers, their limits, and what must be done later: a second rater, 200 labelled Observations, calibration from Prediction outcomes, a psychologist's review).
- First set of Thought Experiments drafted for the owner, plus a short guide: where to source content, how to write and manage them.
- CONTEXT.md terms and ADRs once the design settles.

## Extended by a later grill (25 Nov 2026, issue 23)

`issues/23-situations-vary-on-more-than-people.md` and ADR-0031 extend these decisions; the reasons are there.

- Decision 7 (directness): it will also set where an Exploration starts and how long it waits (issue 40). It still never touches the gate.
- Decisions 9 and 10 (situations and tags): tags are now called Conditions and gain audience, stakes and state going in. A situation is still one Life Thread; Conditions never add situations or points.
- Decision 14 (Explorations): "way" is renamed Approach. "Missing part of life" becomes a "missing Condition" need, worked out by code from a coverage table, and the counter-test moves ahead of it.
- Decision 16 (ready): narrowing uses any Condition, needs 2 clear stories on the side that holds, and at most 2 narrow one Pattern.

## Still open

Nothing from the grill. Next: `/to-prd`.
