# PRD: Moves — the Companion actively helps, and learns what helps each User

Status: ready-for-agent

## Problem Statement

The Companion understands the User but too often doesn't help them.

- In a real chat, the User was looking for app hosting under SGD 15–20 a month with managed Postgres. Every Message was read as Accountability, whose "how to reply" only asks for the next step, so Zeph asked "what's on the shortlist?" five times and handed the work back. It never looked anything up, though it has Web Search.
- The Advice Need fits only when the User asks outright, so a User who is clearly stuck but doesn't say "what should I do?" gets questions, not help.
- The web search tool is told not to be used for advice, only for facts like a quote or an event, so practical legwork is ruled out.
- The Persona leans passive: "follow the person's lead", "hold opinions loosely", "the person makes their own decisions".
- When it does help well (pushing the User to define what "done with internal testing" means), that's luck of the Need's wording. Nothing records what kind of help it was, or whether it worked.
- It never learns what helps this User. "Push helped when they were frustrated" and "Push backfired when they were exhausted" are both lost, so it can't get better at helping someone over time.

Zeph is meant to be a mentor and a solid friend who knows the User intimately: one who suggests, plans, pushes, reframes, calms and grounds, does legwork for everyday tasks, and over time knows what helps *this* person in *this* situation and mood.

## Solution

The Companion now decides two things before each reply: the **Need** (what the User wants) and the **Moves** (what the Companion does about it).

- Each reply has a lead Move and at most one supporting Move, or none (just responding). The starting Moves are Calm, Ground, Reframe, Mirror, Suggest, Plan steps, Push and Research.
- Each Need lists the Moves that never go with it (Be heard rules out Push, Suggest, Plan steps, Research and Reframe), so being active never turns into being pushy at the wrong moment. A Need's "how to reply" now sets tone and stance; the Moves say what to do.
- The Understanding can hold a next Move in mind, with why ("Next: Research, once I know their requirements"), so over a Conversation the Companion works through a sequence: hear them out, then reframe, then plan steps.
- Research does the legwork with Web Search: finding and comparing options against what the User needs. It needs the Web Search Feature. When Web Search doesn't work for the User (a lower plan) or the daily limit is used up, Research is never offered, and the Companion suggests from what it knows and says plainly it can't look things up.
- When a Conversation ends, the Companion keeps **Move Outcomes**: for each Move, the situation, how the User felt, whether it helped, didn't or was mixed, and why. Before each reply the Understanding sees the past Move Outcomes closest to the current situation and mood, so it picks help that has worked for this person in moments like this. The User Portrait's "what has helped and what hasn't" draws on them.
- A next Move left unmade when a Conversation ends may become a Curiosity, so the Companion follows up naturally later.
- Users see their Move Outcomes on the Memories page under "What helps you" and can delete them. Admins manage Moves on their own Dashboard page and test them with Evals.
- The Persona and web search tool wording are updated so the Companion says what it sees and offers help when it can see help would land.

With this, the hosting chat goes: Accountability; lead Research, support Suggest; Zeph names real hosts under SGD 20 with managed Postgres, with sources, by the second or third Message.

## User Stories

### The User being helped

1. As a User, I want the Companion to look up and compare real options when I'm stuck on a practical choice, so that I get help instead of questions back.
2. As a User, I want the Companion to offer help when it can see I'm stuck, even if I didn't ask outright, so that I don't have to phrase things a certain way.
3. As a User, I want the Companion to only listen when I'm venting, so that it doesn't push solutions at me while I'm hurting.
4. As a User, I want the Companion to calm me when I'm anxious or overwhelmed, so that I can think clearly again.
5. As a User, I want the Companion to ground me in what's real and in my control, so that I stop spiralling.
6. As a User, I want the Companion to offer a different angle on a belief that holds me back, so that I can break out of a limiting mindset.
7. As a User, I want the Companion to point out patterns it has seen in my past chats, so that I learn things about myself I hadn't noticed.
8. As a User, I want the Companion to give me concrete options or its real view when I need them, so that I can decide faster.
9. As a User, I want the Companion to break a goal into next steps with a clear finish line, so that my work doesn't keep growing without an end.
10. As a User, I want the Companion to hold me to what I said I'd do and challenge my excuses kindly, so that I follow through.
11. As a User, I want the Companion to combine a small comfort with real help in one reply, so that it feels like a friend, not a tool.
12. As a User, I want the Companion to build on what it did earlier in the Conversation, so that it feels like it has a direction, not random replies.
13. As a User, I want the Companion to change course when I react badly to something, so that it doesn't keep doing what isn't working.
14. As a User, I want the Companion to learn which kinds of help work for me in which situations and moods, so that it gets better at helping me over time.
15. As a User, I want the Companion to remember that something helped before but not to assume it always will, so that it reads how I am today.
16. As a User, I want the Companion to follow up later on something it meant to raise but didn't get to, so that it feels like a friend who remembers.
17. As a User, I want the Companion to say where web information came from, so that I can check it.
18. As a User, I want my personal details kept out of web searches, so that my privacy is safe while it researches for me.
19. As a User without Web Search on my plan, I want the Companion to tell me plainly it can't look things up and still help from what it knows, so that I'm not misled.
20. As a User who has used up today's web lookups, I want the Companion to tell me it can't look things up until tomorrow, so that I know why.
21. As a User, I want the Companion to say what it really thinks, even when it isn't what I want to hear, so that I get honest help.
22. As a User, I want small talk to stay light, so that not every chat turns into self-improvement.
23. As a User asking to change a setting, I want the Companion to just do it, so that it doesn't try to coach me instead.

### The User's memory and privacy

24. As a User, I want to see what the Companion has learned about what helps me, under "What helps you" on the Memories page, so that I know what it keeps.
25. As a User, I want each Move Outcome shown with its situation, how I felt, whether it helped and why, so that I understand it.
26. As a User, I want to delete any Move Outcome, so that it's never used again.
27. As a User, I want my User Portrait rewritten without a Move Outcome I deleted, so that what I deleted doesn't live on in it.
28. As a User with User Memory off, I want no new Move Outcomes kept, so that the Companion stops learning when I ask.
29. As a User with User Memory off, I want the Move Outcomes already kept still used, so that it behaves the same as the rest of User Memory.
30. As a User, I want Delete My Data and Account Deletion to remove my Move Outcomes, so that everything about me goes.
31. As a User, I want Move Outcomes kept after Message Retention deletes old messages, so that the Companion doesn't forget what helps me.
32. As a User, I want Move Outcomes written about the moment and what helped, not judgements of me, so that reading them feels respectful.

### Admins managing Moves

33. As an Admin, I want a Moves page on the Dashboard listing every Move, so that I can see how the Companion can help.
34. As an Admin, I want to add a Move with a name, when it fits and how to do it, so that I can grow what the Companion can do without code.
35. As an Admin, I want to edit a Move's name, when it fits and how to do it, so that I can tune how it helps.
36. As an Admin, I want to delete a Move, so that it's never picked again.
37. As an Admin, I want Move Outcomes that named a deleted Move to keep its name, so that Users' history stays readable.
38. As an Admin, I want to set the order Moves are listed in, so that the list reads sensibly.
39. As an Admin, I want no two Moves to share a name, ignoring case, so that picks are never ambiguous.
40. As an Admin, I want to choose, on each Need, the Moves that never go with it, so that I control when the Companion may push or advise.
41. As an Admin, I want to mark a Move as needing a Feature, so that help tied to a plan only reaches Users who have it.
42. As an Admin, I want a Move whose Feature doesn't work for a User never offered to the Understanding, so that the Companion never plans around something it can't do.
43. As an Admin, I want changes to Moves to reach the next reply, so that I see the effect straight away.
44. As an Admin, I want the Move Outcome keeping prompt, model and thinking setting on the Platform Settings page, so that I can tune how the Companion learns.
45. As an Admin, I want to set how many Move Outcomes reach the Understanding and how close in meaning they must be, so that I can balance relevance against noise.
46. As an Admin, I want to see only how many Move Outcomes a User has, never their content, so that Users' privacy is kept.
47. As an Admin, I want the Model Call Log to show the lead, supporting and next Moves of each Understanding, so that I can see how the Companion chose to help without seeing words.
48. As an Admin, I want every changed and new wording (Moves, Needs, Persona, web search, Understanding and keeping prompts) in the starting settings, so that a fresh install starts active, not passive, and I tune it from there.

### Admins testing with Evals

49. As an Admin, I want Understanding Eval cases to say which lead, supporting and next Moves are allowed for each Message, so that I can check the Companion picks the right help.
50. As an Admin, I want a case to say no Move is expected, so that I can check it just listens or chats when it should.
51. As an Admin, I want a case to give a made-up User past Move Outcomes, so that I can check it uses what helped before, in the right mood.
52. As an Admin, I want Judge rules that check the reply actually did the Move (e.g. named real hosts under SGD 20), so that a right pick with a generic reply still fails.
53. As an Admin, I want starting cases built from the real hosting and internal-testing chats, so that the failures that started this are tested.
54. As an Admin, I want a Variant to override a Move's text, so that I can try new wording before making it live.
55. As an Admin, I want Make Live to apply a Variant's Move overrides, so that a tested change reaches real Users.
56. As an Admin, I want a Move Outcome Eval that gives a finished Conversation and checks the Move Outcomes kept and why, so that I know the Companion learns the right lessons.
57. As an Admin, I want Eval cases for Research with Web Search off, so that I can check the fallback is honest.

## Implementation Decisions

- **Domain model.** Follows ADR-0016 and the updated `CONTEXT.md` terms: Move, Move Outcome, and the changed Need, Understanding, User Memory, User Portrait, Curiosity, Web Search, Eval and Model Call Log.
- **Moves are Admin-managed data (ADR-0004)**, built like Needs: a Moves module in core with its port and repository adapter. A Move has an id, name (unique ignoring case), when it fits, how to do it, list position, and an optional needed Feature (Web Search for Research). There is no fallback Move: no Move is a valid pick.
- **Need gains ruled-out Moves**, a set of Move ids. Deleting a Move removes it from every Need's rule-outs.
- **Starter Moves and rule-outs** are in the seed files. Because seeds load only on first run, a migration adds the starter Moves and each starter Need's rule-outs to an existing database when it has no Moves (following the Check-in Kinds migration). Starter rule-outs: Be heard rules out Reframe, Suggest, Plan steps, Push, Research; Think it through rules out Suggest, Research; Just chatting rules out Calm, Ground, Reframe, Mirror, Plan steps, Push; Get it done and Ask more rule out all of them.
- **All changed and new wording lives in the seed files as the defaults**: the starter Moves, each Need's rule-outs and any Need wording changed to separate stance from action, the Persona, the web search tool description and reply instructions, the Understanding prompt (picking Moves, next Move, using Move Outcomes), the Portrait and Curiosity keeping prompts, and the new Move Outcome keeping prompt. The Persona says the Companion has real views and says them, and is here to help the User grow and get unstuck; "follow their lead" stays for topics. The web search tool description drops "not for advice" and allows practical requirements (like a budget) in queries, never personal details. Once the app is live, Admins change any of it on the Dashboard.
- **Understanding form gains** lead Move, supporting Move, next Move and why. The Understanding is shown only the Moves the picked Need allows and whose needed Feature works for the User, so picking happens alongside the Need, in the same call. An unknown or disallowed Move name in the answer is dropped (treated as no Move) rather than failing the Understanding. The fallback Understanding has no Moves. Earlier Understandings in the Conversation, shown to each Understanding, include their Moves.
- **Feature gating** reuses the existing Feature checks. Research is withheld when Web Search doesn't work for the User or the Web Search Limit is used up for their day.
- **Reply guidance** adds the lead Move's and supporting Move's "how to do it" after the Need's "how to reply". Web tools stay offered on every reply when Web Search works, as today.
- **Understandings stored** gain lead, supporting and next Move names and why. Schema change on the understandings table.
- **Move Outcome** is a new User Memory record: user, Move name, lead or support, situation, how the User felt, result (helped, didn't, mixed), why, when, and an embedding of situation plus feeling. New table, port and repository adapter.
- **Finding Move Outcomes** happens before the Understanding, by closeness in meaning between the incoming Message (with the Conversation so far) and each Move Outcome's situation and feeling, through the existing Embedder port. Admins set how many (new Platform Setting, starting at 3) and the closeness bar (new Platform Setting). Only the User's own are searched.
- **Keeping Move Outcomes** is a new step in the Conversation-end work, alongside Life Threads and Curiosities. It reads the Conversation's messages and Understandings (which name the Moves), runs only while User Memory works, and has its own model, thinking and prompt in Platform Settings (Move Outcome keeping). The prompt says to write about the moment and what helped, never to judge the User. Its model calls are logged under the Conversation-end group.
- **User Portrait** rewriting reads Move Outcomes along with Memory Items, Life Threads and recent Summaries. Deleting a Move Outcome triggers the same rewrite-within-a-minute path as deleting a Memory Item.
- **Curiosity keeping** is shown any next Move left unmade at the end of the Conversation and may turn it into a Curiosity. No new state carries across Conversations.
- **Deletion.** Delete My Data and Account Deletion remove Move Outcomes. Message Retention doesn't. Deleting the Conversation's messages leaves Move Outcomes.
- **Model Call Log shape** for an Understanding adds the lead, supporting and next Move names. No content for Users.
- **Admin API**: list, create, update, delete and reorder Moves; Need create and update accept ruled-out Move ids. Same error kinds as the Needs API (ADR-0011): a duplicate name is a conflict, an unknown Move id is not found.
- **User API**: list own Move Outcomes and delete one. The admin User view adds a Move Outcome count.
- **Dashboard** (through TanStack Query, ADR-0012, and the one API client): an admin Moves page modelled on the Needs page (no design exists in `docs/design/` for it, so it copies the Needs page's look); the Need edit form gains a ruled-out Moves picker and a needed Feature choice on each Move; the Memories page gains "What helps you".
- **Evals (ADR-0013, ADR-0014).** The Understanding Eval case shape gains per-Message `lead_move`, `support_move`, `next_move` and `no_move` expectations and `move_outcomes` in made-up memory. Setting Overrides can change a Move's text, like a Need (not add or remove one). A new Move Outcome Eval case gives a made-up User and a finished Conversation (messages plus the Moves made) and checks with the Judge the outcomes kept, their result and why. Starter cases cover the hosting chat (Research by the second or third Message), the internal-testing chat (Push or Plan steps), venting (no Push), Push that backfired when exhausted, and Research with Web Search off.

## Testing Decisions

- Good tests drive the system from its outside edges and check what comes out: a Telegram update in, the reply and stored Understanding out; a quiet gap in, the stored Move Outcomes out; an HTTP request in, the response and saved state out; a page rendered, what the Admin or User sees. They don't check internal helpers or prompt strings word for word.
- **Telegram webhook seam** (prior art: the Understanding and Life Thread tests, with the scripted chat model, fake embedder and fake clock): Moves offered depend on the Need's rule-outs; a disallowed or unknown Move is dropped; Research is not offered with Web Search off or its limit used up; the lead and supporting Moves' guidance reaches the reply; past Move Outcomes closest to the Message reach the Understanding, and only the User's own; earlier Moves are shown to later Understandings; Moves are stored and appear in the Model Call Log shape.
- **Conversation-end seam** (prior art: the Conversation-end and Curiosity tests): Move Outcomes are kept when User Memory works and not when it's off; the Portrait is given them; an unmade next Move reaches Curiosity keeping.
- **HTTP API seam** (prior art: the Admin Needs and User Memory API tests): Moves create, edit, delete and reorder; duplicate names refused; deleting a Move clears it from Needs' rule-outs; Need rule-outs saved; Users list and delete their Move Outcomes; deletion triggers the Portrait rewrite; Delete My Data removes them; admins see only the count.
- **Migration** (prior art: the Check-in Kinds migration test): starter Moves and rule-outs added to a database with Needs and no Moves; nothing added when Moves exist.
- **Eval runner seam** (prior art: the Eval runner and Understanding Eval helper tests): the new expectations pass and fail as expected; Move overrides apply inside a Variant only; the Move Outcome Eval runs and reports Case Results.
- **Dashboard** (prior art: the Needs page tests with Vitest and React Testing Library, API client mocked): the Moves page lists, adds, edits, deletes and reorders; the Need form saves rule-outs; "What helps you" lists and deletes.
- Evals themselves cost money and are run by the owner on demand, never in the normal checks.

## Out of Scope

- Forgetting a Move Outcome by asking in chat (a Chat Setting Change). It's Dashboard only for now.
- New tools beyond Web Search (reminders, journaling, calendar). Moves are built so these can be added later as Moves that need a Feature.
- Different Moves or weighting per Persona. There is one Persona in the MVP.
- Making Moves plan-tier extras on their own. Only "needs a Feature" is supported.
- Using Moves or Move Outcomes in Check-in decisions, beyond the Curiosity that an unmade next Move may become.
- Changing the existing Needs' "how to reply" wording beyond what's needed to separate stance from action. Admins tune it with Evals.

## Further Notes

- The platform isn't live yet; the owner is the only User, so no backfill of Move Outcomes from past Conversations is needed.
- Built for many Users: Move Outcome look-ups are per User and indexed for similarity search; nothing holds per-User state in one process.
- Running the new Evals costs money; remind the owner before planning or running Eval Runs.
- Started from a grilling session on 2026-11-17; decisions are in ADR-0016 and `CONTEXT.md`.
