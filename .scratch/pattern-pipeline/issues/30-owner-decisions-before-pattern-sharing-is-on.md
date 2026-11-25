# 30 — Owner decisions before Pattern sharing is on for a real User

Status: needs-info
Track: shared
Blocked by: none (needs a decision session with the owner first, see below)

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

## Acceptance criteria

- [ ] Each question above has the owner's answer recorded here
- [ ] Question 5 was checked with a test, and a bug was filed if the quote comes back
- [ ] `CONTEXT.md`, ADRs and `docs/pattern-pipeline/README.md` are updated where a decision changes the design
- [ ] The build work is written as a plan here, or split into issues, and the status set to `ready-for-agent`

## Comments
