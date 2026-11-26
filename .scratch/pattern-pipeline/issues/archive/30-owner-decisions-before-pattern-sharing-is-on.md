# 30 — Owner decisions before Pattern sharing is on for a real User

Status: completed
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (sections 02, 07, 08, 09, 13 and 18), triaged with the owner on 25 Nov 2026. Design: `docs/pattern-pipeline/README.md`.

## Needs the owner's decisions before any solution

Don't plan or build this yet. Go through the questions below with the owner (`/grilling`), record each answer here and, where the domain moves, in `CONTEXT.md` and ADRs. Then write the plan and set this to `ready-for-agent`. It may split into more than one issue.

Pattern sharing should stay off for real Users until the "must decide" list is settled and built.

## Must decide before sharing is on

**1. When the User asks "what patterns do you see in me?", which wins: the free Read or the gate?** (20 → 08)
In the running app the Read stated a suspected Pattern in its own words, with named people, no Prediction and no record. The gate holds only for what code offers. Options from issue 08:

- leave it (the Read is free, decision 6);
- when a suspected or contested Pattern is close to what the Read says, code tells the Reply Plan to say it is still getting to know them;
- stop showing the Agenda's if / then to the Reply Plan.

Then add an Understanding Eval case for it.

**2. One story counts twice.** (20 → 09)
A story that settles a Prediction is also tagged as an Observation, so the score moved about 280 for one event. Which should count? Simplest: when a Conversation settles a Prediction, that Conversation's Observations of the same Pattern Type don't count toward "after sharing" (or count half).

**3. The ruled-out topics list.** (20 → 07)
`pattern_ruled_out_topics` starts as abuse, sexual trauma, self-harm or suicide, eating and body image. It is a guess. The owner corrects it on Platform settings. Also decide: should a topic added later reach Observations already tagged?

**4. Does deleting a Pattern they disagreed with forget the "no"?** (20 → 18)
Today it deletes everything, so Zeph can notice and tell the same Pattern again. Either "delete means forget everything", or keep a small "never again" mark per User and Pattern Type that the ready gate reads (about half a day).

**5. Can a deleted quote come back today?** (20 → 13)
Logged as a future risk "if a Conversation is ever tagged twice". But `make match-patterns` already tags old Conversations again (`_tag_again` in `src/companion/core/pattern_matching.py`). An agent checks this first with a test: delete a quote, tag the day again, is it kept again? If yes, it is a bug in shipped code: file it with `/file-bug` and fix it there.

## Should decide: the numbers and rules of confirming and closing

- **"Strong evidence after sharing" is 300**, a number the agent chose (`pattern_confirm_points_after_sharing`). Confirm or change it. (20 → 09)
- **A shared Pattern can hardly be closed**: ready at 300, closed under −150, one failed Prediction is −140. Add a second rule, such as "closed when more Predictions didn't than did, after N"? (20 → 09)
- **A new Prediction is the same as the last** in other words, so "two came true" is one Prediction twice. Give each Pattern Type two or three Prediction wordings? Catalog work for the owner. (20 → 09)
- **A Prediction nobody answers** is marked "not followed up", counts nothing, and Zeph offers a new one. Is that right? (20 → 09)
- **Scoring counts evidence that only narrows a Pattern**, while the gate leaves it out, so a true narrow Pattern may never become ready. Should scoring use the gate's rule? (20 → 07)
- **Curiosity Check-ins ignore backing off**: a User who brushed off two questions can get a "Something I've been wondering" Check-in the next day. Should backing off hold Check-ins too? (20 → 02)
- **A told Pattern whose Pattern Type left the catalog** can't be seen or deleted on the Patterns tab. Keep the wording on the Pattern when it is shared? Must be done before any Pattern Type is removed. (20 → 18)

## The owner's answers (25 Nov 2026)

Asked one at a time in a `/grilling` session.

| # | Question | Answer |
|---|---|---|
| 1 | Asked "what patterns do you see in me?": the Read or the gate? | **The gate wins.** With nothing ready, Zeph says it is still getting to know them and may talk about one recent situation, never a claim about who they are. With a Pattern ready, the ask is the moment to share it properly. The Agenda's if / then stays shown to the Reply Plan. An Understanding Eval case is added. |
| 2 | One story counts twice | **The Prediction only.** When a Conversation settles a Prediction, that Conversation's Observations of the same Pattern Type count nothing for that Pattern. The quotes are still kept and shown. |
| 3 | Ruled-out topics | The four, plus **addiction**, **sexuality and gender** and **mental health diagnoses**. A topic added later reaches **new Observations only**. |
| 4 | Deleting a Pattern they disagreed with | **Keep a "never again" mark** (User and Pattern Type, none of their words) when the deleted Pattern was one they disagreed with or that didn't hold up. Zeph never notes or shares that Pattern Type for them again. Delete My Data removes the mark. |
| 5 | Can a deleted quote come back? | An agent checks with a test (below). |
| 6 | "Strong evidence after sharing" is 300 | **Keep 300.** |
| 7 | A shared Pattern can hardly be closed | **Closed when 2 Predictions didn't come true and more didn't than did** (the 2 is an Admin setting). Confirmed by Predictions only when more came true than didn't. The score floor stays. |
| 8 | A new Prediction is the same as the last | **Three Prediction wordings per Pattern Type**, each testing a different side; code picks one this User hasn't had. Claude drafts all 45, the owner corrects them, with a guide in `docs/`. |
| 9 | A Prediction nobody answers | Counts nothing and Zeph offers a new one, **but after 2 in a row go unanswered Zeph stops** giving Predictions for that Pattern until the User brings it up (the 2 is an Admin setting). |
| 10 | Scoring counts evidence that only narrows | **One rule for scoring and the gate.** Also: evidence against with no person named no longer switches narrowing off. |
| 11 | Curiosity Check-ins ignore backing off | **Leave it.** Nothing is built. (So the asked check on Curiosity Check-ins, section 27 of issue 20, is not built here either.) |
| 12 | A told Pattern whose Pattern Type left the catalog | **Keep the wording on the Pattern when it is shared**, and show that. |

Added by the owner in the same session:

- **Ask the follow-up when the User next talks about that person or situation**, with the 7 days as the fallback. A fixed wait alone is too passive.
- **Replies are shown the Patterns Zeph has told the User** (being tested and confirmed). Zeph may build its Read on one and name it when today's story fits ("the thing we're testing" for one being tested; plainly for a confirmed one). Never one they disagreed with, never while they are struggling.
- **After each Conversation the backend tracks where each told Pattern showed up** (for or against, with whom, in which Life Thread), with no new model call, and the next replies are told.
- **Reflections** (guided reflection on a confirmed Pattern) is the owner's idea for a new feature: its own issue, `34-reflections-on-a-confirmed-pattern.md`.

## The build, split into issues

| Issue | What | From |
|---|---|---|
| `35-deleted-quote-comes-back-when-its-day-is-tagged-again.md` | Bug: a deleted quote is kept again when its day is tagged again | question 5 |
| `36-a-shared-pattern-is-confirmed-and-closed-fairly.md` | One story counts once, closing on failed Predictions, a stop after unanswered ones, one narrowing rule | answers 2, 6, 7, 9, 10 |
| `37-what-a-user-deletes-or-was-told-stays-that-way.md` | "Never again" mark, the wording a User was told, the ruled-out topics | answers 3, 4, 12 |
| `38-predictions-test-different-sides-and-are-followed-up-in-time.md` | Three Prediction wordings per Pattern Type, follow-up when they next talk about it, the owner's guide | answer 8, added item |
| `39-replies-know-the-patterns-zeph-told-and-the-gate-holds-when-asked.md` | Replies are shown told Patterns and where they showed up; the gate wins when asked; an Eval case | answer 1, added items |
| `34-reflections-on-a-confirmed-pattern.md` | Reflections, the owner's idea: needs its own decision session | added item |

Order: 35, 36, 37, 38, 39, on one branch (`pattern-30-owner-decisions-before-sharing`), one commit per issue.

**Question 5, checked (25 Nov 2026):** yes, a deleted quote comes back. `test_a_quote_the_user_deleted_is_not_kept_again_when_its_day_is_tagged_again` kept 1 Observation where 0 were expected. Filed as issue 35.

## Acceptance criteria

- [x] Each question above has the owner's answer recorded here
- [x] Question 5 was checked with a test, and a bug was filed if the quote comes back
- [x] `CONTEXT.md`, ADRs and `docs/pattern-pipeline/README.md` are updated where a decision changes the design
- [x] The build work is written as a plan here, or split into issues, and the status set to `ready-for-agent`

## Comments

### 25 Nov 2026: closed

**Evidence per criterion**

- **Each question has the owner's answer recorded.** The table "The owner's answers (25 Nov 2026)" and the list under it.
- **Question 5 was checked with a test, and a bug filed.** The test was red (a deleted quote was kept again); filed and fixed as `archive/35-deleted-quote-comes-back-when-its-day-is-tagged-again.md`.
- **`CONTEXT.md`, ADRs and the pipeline README are updated.** `CONTEXT.md` (Pattern, Prediction, Read), ADR 0030 (the gate holds when a User asks), `docs/pattern-pipeline/README.md` ("Changed (25 Nov 2026)"), `lifecycle.md`, `tagging.md`, `docs/message-pipeline/README.md`.
- **The build was split into issues.** 35 to 39, all built on this branch and archived; 34 (Reflections) waits for the owner.

Answer 11 ("leave it") built nothing. What is left for the owner is in `20-findings-for-the-owner.md`, section 30.

## Completion

- Completed: 2026-11-25
- Commit: efe99ea5 ("Merge pattern-30-owner-decisions-before-sharing: the owner's decisions before Pattern sharing is on", the merge of pattern-30-owner-decisions-before-sharing into main; work commits b4fdc35d, 351f74c8, ec11f7a8, e21f096b, f9225f60, 7522ee99, 45d716a0, cc0fd499, ff840919, 875f3175, 88bc0a4a)
