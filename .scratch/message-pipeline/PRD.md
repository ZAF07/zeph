# PRD: Reads and Patterns: Zeph understands, forms a view, and helps people see themselves

Status: ready-for-agent

## Problem Statement

In a real 48-minute Conversation (19 Nov 2026, 17:20), the owner talked to Zeph about guilt over their mum's visit, about quitting their job with only two months of savings, and about a product manager who bulldozes every discussion. Zeph mirrored their words back in 16 of 26 replies, closed the Conversation mid-rant ("The rant's out now, though. How's your evening looking?"), repeated the same advice twice when asked "Don't you have opinions?", and only gave a useful view ("the PM, the project and the impatience with your mum are the same thing") after being pushed three times. The User's verdict: "You haven't really been useful to me at all" and "This platform is not ready for people to use."

From the User's side:

- Zeph listens but rarely has anything to offer. It hands their thoughts back as questions instead of saying what it sees.
- It cuts in at the wrong moments. A rant typed over ten texts got five replies, each landing mid-sentence, and a Check-in was slipped in just as the rant ended, which felt like being brushed off.
- It doesn't join the dots. Everything needed for the useful view (hyperfocus, the mum's visit, the job) was already in User Memory, as separate pieces nothing linked.
- It forgets the Conversation they were just having. Fifteen minutes of quiet and Zeph keeps only a short Summary, so "as I was saying…" doesn't work.
- What it keeps is thin where it matters. After 17 Conversations, Values & beliefs has 0 items and Goals has 2; commitments ("I'll call mum tonight") aren't kept at all, so Zeph never asks how they went.
- The Dashboard shows several vague Summaries a day ("they critiqued Zeph and their platform") that won't make sense months later.

Behind this: one Understanding call does about twelve jobs and once contradicted itself (wrote "rather than another mirror" and picked Mirror); a separate Check-in model gives the reply its own order; the reply gets a flat stack of instructions with no priority; and nothing in the pipeline asks Zeph to form a view at all.

For Admins: there is no way to steer how Zeph sees people, so any view it does form comes from the model, not from them; and 64 of 76 editable settings, including the Persona and every prompt, have no hint saying what they are for.

## Solution

Zeph's job in every reply that matters becomes: understand the User, form an honest **Read** of what is really going on, from the **Outlook** Admins write, and help them move. How the User feels decides when and how gently Zeph says it, not whether it has a view.

The reply path is rebuilt as small, one-job steps (ADR-0021): the Safeguard; a longer wait for the end of the **Message**, starting over if a text lands before any of the reply has gone out; the reply gate; the **Understanding** (what they said, mean, feel and want, keeping said, read and unclear apart, deciding nothing); **Recall** (plain code, wide, by meaning); the **Reply Plan** (the Read, the Need and Moves, what the reply uses, whether a Woven-in Check-in fits, and where the Conversation is now); and the **Reply**, which follows a strict priority order with optional extras last. Every reply sees all messages from the last 24 hours across Conversations, and the Reply Plan can read a past day's messages word for word while Message Retention keeps them.

**Patterns** become a new kind of User Memory: what keeps showing up across a User's Life Threads, including what they keep choosing (their values). Kept when a Conversation ends, from linked and closest Threads however old, re-reading the days behind their evidence. Suspected Patterns are hidden and only offered as Zeph's view (ADR-0020); the User's reaction in chat confirms or closes them; confirmed ones show on the Dashboard with their evidence, so Users discover things about themselves they hadn't put into words.

**Day Summaries** replace per-Conversation Summaries: one per User per day, rewritten from all of that day's messages each time a Conversation ends, carrying feeling as well as facts. Commitments the User agrees to go into their Life Thread and get a hidden follow-up Curiosity. Every Admin-editable pipeline field explains itself with a short hint.

The full design and every decision are in `docs/message-pipeline/README.md`; terms are in `CONTEXT.md`.

## User Stories

### Being understood

1. As a User, I want Zeph to wait until I've finished typing my thought across several texts, so that it answers what I meant, not half of it.
2. As a User, I want Zeph to start over if I send another text before its reply has gone out, so that its reply covers everything I said.
3. As a User, I want a text I send after part of Zeph's reply has already arrived to start a new Message, so that nothing I say is lost or answered twice.
4. As a User, I want Zeph to read a short "yep" or "fine" in the light of the whole Conversation, so that it notices when a rant is spent or I'm closing up.
5. As a User, I want Zeph to act on what I actually said and not on its guesses, so that it doesn't confidently misread me.
6. As a User, I want Zeph never to tell me how I feel as if it knew ("you're really hurt"), so that I don't feel labelled.
7. As a User, I want Zeph to check what is unclear when it matters (do I want advice or just to vent?), so that it doesn't guess wrong.
8. As a User in crisis, I want the Crisis Reply at once, whatever else I'm typing, so that help is never held back by the wait.

### Getting a real view

9. As a User, I want Zeph to have an honest view of what's going on with me, so that talking to it gives me something I couldn't get from my own head.
10. As a User venting, I want Zeph to hear me out first, so that I'm not fixed before I've finished.
11. As a User whose vent is spent, I want Zeph to then say what it sees, so that it doesn't keep mirroring me.
12. As a User, I want Zeph's view to add something I haven't said (a link between things, or a real answer to my question), so that it isn't my words handed back.
13. As a User who asks "thoughts?" or "don't you have opinions?", I want Zeph's deepest view straight away, not the advice it already gave, so that I don't have to push three times.
14. As a User, I want Zeph not to repeat the same view twice in a Conversation, so that it doesn't preach.
15. As a User who pushed back on something Zeph noticed about me, I want it to wait a good while before raising it again, so that I don't feel nagged.
16. As a User who is just chatting lightly, I want Zeph to keep it light, so that not every message becomes a session.
17. As a User, I want Zeph to say its view gently when I'm tender and plainly when I'm asking, so that it lands.
18. As a User, I want Zeph to offer what it notices as its view ("here's what I notice…"), never as fact, so that I can disagree.

### Not being interrupted

19. As a User mid-rant, I want Zeph never to slip in a Check-in, a breathing prompt or a change of subject, so that I don't feel brushed off.
20. As a User, I want a due Check-in woven in only when it truly fits what we're talking about, so that it feels like a friend drifting onto a side topic.
21. As a User asking a direct question, I want it answered first, before anything else Zeph wants to bring up.
22. As a User, I want Zeph to know where our Conversation is (venting, thinking it through, asking for a view) and hold or push accordingly, so that it doesn't flip approach every message.

### Patterns: seeing myself

23. As a User, I want Zeph to notice what keeps showing up across different parts of my life, so that it can help me see what I can't see myself.
24. As a User, I want Zeph to notice the pattern when I'm doing it somewhere new, even about something I've never talked about before, so that the moment it matters is the moment it's named.
25. As a User, I want Zeph to learn what I value from what I keep choosing, not only from what I say, so that it understands what matters to me.
26. As a User, I want things Zeph only suspects about me kept out of sight until I agree with them, so that I'm never shown half-formed guesses about myself as facts.
27. As a User, I want my reaction to what Zeph noticed to count (agreeing confirms it, rejecting closes it for good), so that Zeph's picture of me is one I recognise.
28. As a User, I want to see the Patterns I've confirmed on the Dashboard with the moments that show them, so that I can reread what I've learned about myself.
29. As a User, I want to delete any Pattern, so that Zeph stops using it.
30. As a User, I want things I talked about months ago to still count toward a Pattern, so that Zeph sees my whole life, not just last week.
31. As a User, I want my User Portrait to include only Patterns I've confirmed, so that what I read about myself is what I've agreed with.
32. As a User, I want Delete My Data and Account Deletion to remove all my Patterns, suspected ones included, so that nothing about me is left behind.

### Being remembered

33. As a User coming back after a break, I want Zeph to remember exactly what we said earlier today, so that "as I was saying…" works.
34. As a User coming back the next morning, I want Zeph to still see last night's messages, so that midnight doesn't wipe the slate.
35. As a User asking about something from a week ago, I want Zeph to look at what we actually said that day, so that it doesn't guess.
36. As a User, I want Zeph to tell me plainly when something is too old for it to have the exact words, so that it doesn't make them up.
37. As a User, I want all the Threads that matter to be in mind at once, not just three, so that Zeph can join them.
38. As a User, I want something I said early in a long Conversation to still be in mind at the end of it, so that Zeph doesn't lose the start.
39. As a User, I want each thing Zeph learns kept in one place (a fact, a story or a pattern), so that it isn't confused by the same thing written four ways.

### Commitments and goals

40. As a User who says "ok, I'll call mum tonight", I want Zeph to remember it, so that it can ask how it went.
41. As a User, I want Zeph to ask how a commitment went only after its day has passed, so that it isn't nagging.
42. As a User, I want only things I agreed to treated as commitments, not every suggestion Zeph made, so that I'm not held to what I never said.
43. As a User, I want to see my commitments and how they went in the story of their Life Thread, so that I can see my own follow-through.
44. As a User, I want goals I show plainly kept as Goals even when I never said "my goal is", so that Zeph knows what I'm working toward.

### Day Summaries

45. As a User, I want one Summary per day on the Dashboard, not one per Conversation, so that my history is easy to read.
46. As a User, I want the day's Summary updated each time I talk that day, so that it always covers the whole day.
47. As a User, I want a Conversation that runs past midnight counted in the day it started, so that it isn't split.
48. As a User, I want my Day Summaries to say what happened, how I felt and why, and what it meant to me, so that rereading one months later still makes sense.
49. As a User, I want my day to be "my day" in my own time zone, like the Daily Message Limit, so that it matches my life.
50. As a User, I want to delete a Day Summary, so that Zeph forgets that day's account.

### Admins steering Zeph

51. As an Admin, I want to write Zeph's Outlook (how it sees people and what helps them grow) as one piece of prose apart from its voice, so that I decide who Zeph is.
52. As an Admin, I want Zeph's Reads to come from the Outlook and never from views the model makes up, so that the same situation is read the same way every time.
53. As an Admin, I want an Outlook change to apply from the next reply, so that I can tune Zeph quickly.
54. As an Admin, I want the Reply Plan's prompt, model and thinking switch editable like the other core services, so that I can tune it.
55. As an Admin, I want the Pattern keeping prompt, model and thinking switch editable, so that I can tune how Patterns are found.
56. As an Admin, I want to set how long Zeph waits for the end of a Message, so that I can balance speed against cutting Users off.
57. As an Admin, I want to set how many Threads and Patterns can be in mind at once (high, for cost), so that Zeph has enough to join the dots.
58. As an Admin, I want to set how many hours of messages every reply sees, so that I can balance memory against cost.
59. As an Admin, I want to set how many related Threads and days the Pattern step looks at, so that its cost stays fixed.
60. As an Admin, I want to set how long a Pattern the User pushed back on waits before Zeph offers it again.
61. As an Admin, I want every editable pipeline field (the Persona's voice and Outlook, each prompt, model, thinking switch and limit, and the fields of each Need, Move and Check-in Kind) to show a short hint saying what it is, what it serves and how it is used, so that I know what I'm changing.
62. As an Admin, I want the Model Call Log to show each reply's Understanding, Reply Plan and Reply as separate steps, with the shape of the Reply Plan's decision (Need, Moves, whether a Read was formed and said, whether a Pattern was used, whether a Check-in was woven in), so that I can see what drove a reply without seeing any User's words.
63. As an Admin chatting with Zeph myself, I want full content in my own traces, including the Read, so that I can see exactly why it replied as it did.
64. As an Admin, I want Woven-in Check-ins still logged as before (sent with their Kind, marked woven in, taken back if the reply fails), so that the Check-in Log stays true.
65. As an Admin, I want a User's confirmed Pattern count visible (not their content), so that I can tell Patterns are working without reading private things.

### Quality

66. As an Admin, I want a Day Summary Eval that checks a Summary can answer questions about the facts, the feelings and what Zeph offered on its own, so that I can tune the Summary prompt with evidence.
67. As an Admin, I want the Understanding and the Reply Plan checked by separate Evals, so that I can tell which job went wrong.
68. As an Admin, I want existing Understanding Eval cases kept and moved to whichever step now owns each check, so that past work isn't lost.
69. As an Admin, I want to be reminded that Evals cost money before running them, so that I spend on purpose.

## Implementation Decisions

### Persona and Outlook
- The Persona becomes two Admin-editable texts: its voice (today's Persona text) and its Outlook (new, plain prose). The voice goes in front of the calls that speak to the User (the Reply and Check-ins sent on their own); the Outlook goes only into the Reply Plan's instructions. The Understanding gets neither.
- A starting Outlook is seeded and Admin-editable afterwards (ADR-0004).

### Message wait and starting over
- The Message wait setting stays Admin-set, with a longer default (about 15 seconds instead of 5).
- If a text arrives while a reply is being prepared and before any part of it has been sent, the reply in progress is dropped and the Message is answered again with every text in it. A Woven-in Check-in already saved for the dropped reply is taken back through the existing take-back path. Once part of a reply is sent, a new text starts the next Message, as today.
- This works within the in-memory per-User queue (ADR-0018); no change to how many backend processes run.

### The reply path (ADR-0021)
- **Understanding** (existing core service, narrowed): its prompt is rewritten to read only. It is given the Message, every message from the last 24 hours across Conversations, the earlier Understandings, and the User Portrait. Its output: what the User said and means; how they feel and how strongly, and what they want, each split into said / read / unclear; whether the cause is known; whether they are struggling; whether they asked for a photo; and short phrases for past things to look up. It no longer picks Needs, Moves, Threads, Curiosities, Knowledge or memory categories. When it fails, a fallback Understanding is used, as today.
- **Recall** (plain code): searches by meaning on what the Understanding says they mean plus a wider window of the User's recent texts (Admin-set number, larger than today's 3). It brings in Life Threads and Patterns (Patterns through their linked Threads and directly by closeness), Memory Items, Move Outcomes, due Curiosities and older Day Summaries for the look-up phrases. Whatever passes each closeness bar comes in, capped by a high Admin-set number. The Threads and Patterns that came to mind are kept for the Conversation, so later Messages still have them.
- **Reply Plan** (new core service with its own prompt, model and thinking switch, thinking on by default): given the Outlook, the Understanding, everything recalled, the earlier Reply Plans in the Conversation, the Needs and Moves (those allowed by Features and limits, as today), due Check-in Kinds without fixed behaviour when a Woven-in Check-in is due, and the Ready Knowledge documents with their "when it helps". Its output: the Read; whether to say it now; a one-line "where the Conversation is now"; the Need; lead, supporting and next Moves with why; Threads to bring up or leave alone, with reasons; a Pattern to use and whether it is offered aloud; Curiosities to raise; Knowledge documents and a search phrase, or none; whether a Shared Photo may be sent; whether to ask why; and whether a Woven-in Check-in fits, with its Kind and a note, or not.
- The Reply Plan has one tool: read a past day's messages (by date, the User's own, within Message Retention). Its calls are logged like other tool calls.
- Existing code-enforced rules keep applying to the Reply Plan's choices as they did to the Understanding's: Moves that ask a question, the ask-why rules, Curiosity raise limits, Thread hold-backs, the fallback Need, and Moves needing Features.
- Knowledge passages are fetched after the Reply Plan (plain code), from the documents and phrase it picked.
- The separate Woven-in Check-in model call is retired; its prompt setting is removed. Saving, logging, moving the Due Time and taking back a Woven-in Check-in work as today. Check-ins sent on their own keep their own decision and prompt.
- **Reply**: its instructions are the Persona's voice, the response prompt, then the Reply Plan's sections in a fixed priority order: (1) safety, privacy and the User's own boundaries; (2) what they just asked or need now; (3) the Need, the Moves and the Read if it is to be said; (4) what the plan picked from memory, with nothing suspected stated as fact; (5) the voice; (6) optional extras (a Woven-in Check-in, a Curiosity, Knowledge, a sticker, a Shared Photo), each to be dropped if it doesn't fit. Its history is every message from the last 24 hours across Conversations (Admin-set hours); on a very heavy day the oldest part is replaced by the Day Summary. Reply thinking stays off by default; the switch stays.
- A new Conversation that starts within the window sees the previous Conversation's messages and its last Reply Plan's "where we are" line through the window.
- The Conversation and its quiet gap keep their meaning for Check-ins, per-Conversation limits and when learning runs.

### Patterns (new User Memory, ADR-0020)
- New stored kind, per User: the pattern (a sentence or two); its linked Life Threads; its evidence entries (day, Thread, one self-contained line on what happened); its state (suspected, confirmed, closed); when it was last offered and how the User took it (agreed, pushed back, brushed off); and an embedding for finding it by meaning. No separate "how sure" score.
- A new Conversation-end step runs after Life Threads, with its own prompt, model and thinking switch. It is given the Threads the Conversation touched plus the User's other Threads closest in meaning (open or settled, however old, up to an Admin-set number), the User's existing Patterns, and the days behind the evidence in play (up to an Admin-set number): their messages while Message Retention keeps them, their Day Summaries after. It may add evidence, start a suspected Pattern when the same way of thinking, feeling, acting or choosing shows up across two or more Threads, and confirm or close a Pattern from how the User took a Read offered from it in this Conversation.
- Inferred values and inferred goals are Patterns. The Values & beliefs category holds only values the User has said themselves.
- No Curiosity is ever made to check a Pattern.
- A Pattern closed by the User is never offered again. A pushed-back Pattern waits an Admin-set time before it may be offered again.
- The User Portrait is rewritten from confirmed Patterns too (never suspected ones). Deleting a Pattern rewrites the Portrait within a minute, as for other memory deletions.
- Delete My Data and Account Deletion remove all Patterns; Message Retention doesn't. While User Memory is off, no Patterns are started or changed, and existing ones are still used.
- The Dashboard's Memories page gets a section for confirmed Patterns with their evidence, each deletable; its Copy slots are added to the Memories tab (ADR-0019). Admins see only how many confirmed Patterns a User has.

### One home for each thing learned
- The memory-keeping and Thread-keeping prompts say: a fact is a Memory Item, a story is a Life Thread, and what recurs across stories is left for the Pattern step. The seeded Challenges category description drops "patterns". No backfill of existing memory (the platform isn't live).

### Day Summaries
- Conversation Summaries become Day Summaries: one per User per day (their time zone), keyed by User and day instead of by Conversation. Each Conversation end rewrites the day's Summary from all of that day's messages, not from the old Summary. A Conversation belongs to the day it started.
- The memory-processing prompt asks for the facts (who, what, numbers, decisions, what Zeph advised and how the User answered) and the feeling (how they felt and why, what it meant to them, how their mood moved and what moved it).
- The newest few still go into every reply, and older ones are still found by meaning, each with its date.
- The Dashboard's past-Conversations list shows one entry per day, deletable as today.
- Existing Summaries from the same day are joined into one by migration, with no model rewrite (the platform isn't live).

### Commitments and Goals
- The Life Thread keeping prompt adds commitments the User agreed to (never ones Zeph only suggested) to the Thread's story with their date, and later how they went.
- The Curiosity keeping prompt makes a follow-up for each new commitment, not before the day after it was due.
- The memory-processing prompt keeps goals the User shows plainly in Goals, not only ones said word for word.

### Admin settings
- New Admin settings, each with a hint: the Outlook; the Reply Plan's prompt, model and thinking switch; the Pattern keeping prompt, model and thinking switch; the number of recent texts Recall searches on; the cap on Threads and Patterns in mind; the reply window in hours; how many related Threads and days the Pattern step looks at; how long a pushed-back Pattern waits.
- Every editable pipeline setting, and every field on the Needs, Moves and Check-in Kinds pages, gets a one-or-two-sentence hint: what it is, what it serves, and which step reads it.
- The unused memory retrieval prompt setting is removed.

### Model Call Log
- New steps: Reply Plan and Pattern keeping. The Reply Plan's shape: the Need, the lead, supporting and next Moves, whether a Read was formed and said, whether a Pattern was used or offered, how many Threads were brought up, left alone and held back, whether a Check-in was woven in, whether the past-day tool was used. The Understanding's shape: intensity, whether the cause is known, struggling, how many look-ups. Never any User's words; full content only for Admins' own chats and Evals (ADR-0010).

## Testing Decisions

- Good tests check behaviour from the outside: what the User is sent, what each model call was given, and what the Dashboard and Admin APIs show afterwards. Not how a module is put together inside.
- **Main seam: the Telegram webhook, end to end**, with real Postgres and the existing fakes for the model (the scripted chat model, which records every call's instructions and input), Telegram, the clock and the embedder. Prior art: the Woven-in Check-in, post-conversation, Life Thread, Curiosity, Move Outcome and Understanding tests. This covers:
  - the longer wait, and starting over when a text arrives before any part of the reply is sent (including a Woven-in Check-in being taken back)
  - the Understanding getting no Needs or Moves; the Reply Plan getting the Outlook, everything recalled and due Check-in Kinds; the Reply getting the voice and the sections in priority order
  - wide recall, and Threads and Patterns staying in mind for the Conversation
  - Woven-in Check-ins coming from the Reply Plan, logged as before, and the old Check-in model never being called
  - the 24-hour window across Conversations and across midnight; the past-day tool within and beyond retention
  - Patterns kept at Conversation end from touched and closest Threads; evidence; suspected / confirmed / closed; the push-back wait; never shown before confirmation; removed by Delete My Data; the Portrait using confirmed ones only
  - one Day Summary per day, rewritten on each Conversation end, a midnight-crossing Conversation in the day it started
  - commitments in the Thread story with a follow-up Curiosity not before the next day
  - the Model Call Log shapes for the new steps, and setting hints in the Admin settings API
  - the scripted chat model learns to tell the Reply Plan and Pattern keeping calls apart by their instructions, with harmless defaults, as it does for the other steps
- **Dashboard components** (Vitest + React Testing Library, as today): the confirmed Patterns section with evidence and delete; one Day Summary per day; hints shown under Admin fields.
- **Evals** (the existing Eval runner and case tests, with a fake model so nothing costs money): the Day Summary Eval's case shape, the Judge's questions from the Summary alone, and passing only when answers match the messages; the Understanding Eval split into Understanding and Reply Plan checks, with existing cases' expectations moved to the step that now owns them.
- Migrations get tests as today (prior art: the moves and understanding migration tests): Day Summaries joined per day, the new settings seeded, the Woven-in Check-in prompt and unused memory retrieval prompt removed.

## Out of Scope

- Confirming suspected Patterns on the Dashboard ("Is this you?"); parked as a possible future Feature in ADR-0020.
- Several Personas for Users to choose from; the Outlook is per Persona, but the MVP keeps one.
- Linking Patterns to Move Outcomes (what helps with each Pattern).
- A fast path that skips the Understanding for simple messages.
- Switching Reply thinking on for hard moments.
- Raising Message Retention, or keeping messages past it for Patterns.
- A database-backed message queue or running more than one backend process.
- A Pattern keeping Eval (worth adding once Patterns exist; not designed yet).
- Backfilling existing memory into Patterns or the one-home rule.

## Further Notes

- Source of truth for the design: `docs/message-pipeline/README.md` ("Decisions at a glance" first). Terms: `CONTEXT.md` (Outlook, Read, Reply Plan, Pattern, Day Summary; Understanding, Message, Conversation, Life Thread and Curiosity updated). Decisions: ADR-0016 (Needs and Moves), ADR-0017 (guesses are Curiosities), ADR-0020 (suspected Patterns), ADR-0021 (small one-job steps).
- Suggested build order: Check-ins as an option plus the Reply's priority order first (small, and they stop the worst moment of the review on their own); then the Message wait and starting over; then the Understanding / Reply Plan split with the Outlook; then the 24-hour window and past-day tool; then Day Summaries; then Patterns and their Dashboard section; then commitments and hints.
- Replies will take longer (about 30 to 40 seconds after the last text, with the longer wait and the chained steps). Accepted: a friend reads all your texts before answering. Worth watching in the Model Call Log.
- Each reply carrying 24 hours of messages costs more tokens on busy days; DeepSeek caches repeated prompt beginnings, and the Day Summary stands in for the oldest part on very heavy days.
- Evals cost money; design them freely but run them only when the owner chooses.
- Every acceptance criterion needs a `/run` check in the running app before it is ticked.
