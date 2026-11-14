# PRD: Understanding — the Companion knows the User and works out what they need before replying

Status: ready-for-agent

## Problem Statement

Chatting with the Companion still feels slightly empty. It answers what was just said, but it doesn't feel like it *knows* the User.

- It goes straight from "here is everything" to one reply. It never stops to work out what the User needs right now: to be heard, to think something through, advice, accountability on a Goal, or simply to chat. A rant can get advice; a slip on a Goal can get a lecture.
- It forgets. Only the three newest Conversation Summaries reach a reply. Anything older is gone unless it happened to become a Memory Item, so "how did that job interview go?" weeks later finds nothing.
- It is never *reminded* of anything. When the User says "my sister's wedding is next week", a friend would remember the falling-out with that sister nine months ago and ask how things are now. The Companion only answers the wedding.
- It doesn't notice patterns across Conversations (the same Sunday-night low every fortnight), what has helped this User before, or what annoys them.
- It never wonders about the User. A friend has things they've been meaning to ask; the Companion has none.
- Knowledge is pulled in by matching only the newest text, so "yeah, exactly" finds nothing useful and a vent can get a passage of Seneca.
- It has no idea what it has already said: it could raise the same thing twice, or keep poking a topic the User dodged.
- Admins can't see what the models were given or how they decided, so a flat reply can't be debugged or steered.

The Companion is meant to be a life coach, therapist, accountability partner and close friend who knows the User well. Without knowing the User, it gives them little value.

## Solution

Before every reply the Companion makes an **Understanding**: a private read of what the User just said. Before that read, it is automatically **reminded** of the User's **Life Threads** that the Message touches (by a person or thing named, or by meaning), however long ago they were. The Understanding sees the User's **User Portrait**, their Goals, the newest Conversation Summaries, the reminded Threads, the **Curiosities** whose day has come and this Conversation's earlier Understandings. It then decides:

- which **Need** fits (Admin-managed: Be heard, Think it through, Advice, Accountability, Ask more, Just chatting), plus a sentence of nuance;
- what from the past to bring up (lead with it, weave it in) or leave alone, and why;
- whether their mood stands out without a known cause, so the Companion should gently ask;
- what else to look up: older Summaries by meaning, and whether Knowledge fits at all and from which documents.

The code then fetches what it asked for and the reply is written with the picked Need's "how to reply" guidance and only the context that matters. Each Understanding is saved, so the Companion knows within a Conversation what it already raised and how the User's mood is moving.

When a Conversation ends, the Companion also updates the User's Life Threads (open or settled, and how the User took each bring-up), rewrites their User Portrait (who they are, what's going on, recurring themes, what helps and what doesn't, where they stand on their Goals), and writes new Curiosities (things to ask later, with a "not before" day). Summaries now also record what the Companion offered and how it landed. A new Check-in Kind, "something I've been wondering", can open a Conversation with a Curiosity.

Users see their Portrait and Life Threads on the Memories page and can delete them; deleting really forgets (the Portrait is rewritten without it, and Curiosities it led to are removed). Curiosities and Understandings are internal, but Delete My Data and Account Deletion remove them, and the messaging is plain: User Memory off never deletes anything, it only stops learning.

Admins steer it all from the Dashboard without a redeploy: Needs, the Understanding prompt and model, closeness bars, Curiosity limits, and each Knowledge Document's "when it helps" description. A new **Model Call Log** shows every model call per Message or Check-in: content-free for every User, and with full content only for Admins' own chats and Evals.

Under the hood, replies move out of LangGraph into plain core code (ADR-0009).

## User Stories

### Feeling understood

1. As a User, I want the Companion to work out what I need before it replies, so that its reply fits the moment instead of only my words.
2. As a User who is venting, I want the Companion to listen and reflect back without advice or silver linings, so that I feel heard.
3. As a User who is thinking something through, I want good questions rather than answers, so that I reach my own understanding.
4. As a User who asks for advice, I want a real view or ideas, so that I get help when I ask for it.
5. As a User who slipped on a Goal, I want the Companion to hold me to it kindly but honestly, so that it is a real accountability partner.
6. As a User making small talk, I want the Companion to keep it light, so that not every chat turns deep.
7. As a User whose message is unclear, I want the Companion to ask before going deeper, so that it doesn't guess wrong.
8. As a User whose mood shifts within a Conversation, I want each reply to fit how I am now, so that the Companion keeps up with me.
9. As a User who seems unusually up or down for no reason I've said, I want the Companion to gently ask what's going on, in its own voice, so that it cares about the why.
10. As a User who is venting, I want the Companion not to probe me with questions about my mood, so that it doesn't interrupt me.
11. As a User, I want the Companion not to ask "what's going on?" twice in a row, so that it doesn't feel like an interview.
12. As a User messaging at 2am on a Sunday, I want the Companion to take the time and day into account, so that it reads me like a friend would.

### Being remembered

13. As a User, I want the Companion to remember stories from my life across Conversations, so that I don't have to repeat myself.
14. As a User, I want the Companion to be reminded of an old story when I mention someone or something in it, even months later, so that it feels like a friend who remembers.
15. As a User who mentions my sister's wedding, I want the Companion to recall our old falling-out and ask how things are with her now, so that it sees the bigger picture of my life.
16. As a User talking about something close to an old story without naming it, I want the Companion to still be reminded of it, so that recall doesn't depend on exact words.
17. As a User, I want unfinished stories (open Threads) to matter more than settled ones, so that the Companion follows up on what's still going on.
18. As a User who mentioned a presentation on Thursday, I want the Companion to ask how it went once Thursday has passed, when it fits, so that it follows up like a friend.
19. As a User, I want the Companion to bring up past things only when they fit, not every message, so that it feels natural rather than robotic.
20. As a User who is struggling with something else, I want the Companion to leave a painful old topic alone, so that it has good timing.
21. As a User, I want the Companion not to raise the same story twice in a Conversation, so that it doesn't feel scripted.
22. As a User who brushed off a topic, I want the Companion to wait a good while before trying again, so that it respects my cues.
23. As a User who asked the Companion to drop a topic, I want it never to raise it again unless I do, so that I can trust it.
24. As a User who asks "how did that job interview go, did I tell you?", I want the Companion to find that Conversation however old it is, so that deliberate questions about the past work.
25. As a User, I want the Companion to have a sense of who I am as a whole, so that its replies come from knowing me, not just facts about me.
26. As a User, I want the Companion to notice themes I keep coming back to, so that it can help me see my own patterns.
27. As a User, I want the Companion to learn what helps me and what doesn't (e.g. pep talks annoy me, walks help), so that it supports me the way that works for me.
28. As a User, I want the Companion to know where I stand on my Goals, so that accountability is grounded in what's real.

### Curiosities

29. As a User, I want the Companion to have things it's been meaning to ask me, so that it feels like it thinks about me between chats.
30. As a User who starts a Conversation, I want the Companion sometimes to open with something it's been wondering about me, so that I feel remembered.
31. As a User, I want the Companion to weave a question it's been saving into the Conversation when it fits, so that it doesn't feel like a checklist.
32. As a User, I want a sensitive question to wait for the right moment, so that the Companion is tactful.
33. As a User who gets Check-ins, I want an occasional "something I've been wondering" Check-in, so that reaching out feels personal.
34. As a User, I want at most a few saved questions raised per Conversation, so that I'm not quizzed.
35. As a User who deletes a memory, I want any question it led to removed too, so that the Companion never asks about something I told it to forget.

### Knowledge

36. As a User, I want Knowledge brought in only when it genuinely fits, so that I don't get a lecture when I vent.
37. As a User replying "yeah, exactly", I want any Knowledge to fit the whole Conversation, not my last two words, so that it's relevant.
38. As a User, I want only passages that closely fit, so that the Companion doesn't force a quote.

### Seeing and controlling my memory

39. As a User, I want to see what the Companion thinks it knows about me (my Portrait) on the Memories page, so that nothing is hidden about how it sees me.
40. As a User, I want to see the ongoing stories it follows in my life, open or settled and when last updated, so that I know what it remembers.
41. As a User, I want to delete a Life Thread, so that the Companion forgets that story.
42. As a User, I want to delete my Portrait, so that it stops using that picture of me.
43. As a User who deletes a Memory Item or Thread, I want my Portrait rewritten without it right away, so that the deletion is real.
44. As a User, I want to say "forget the thing about my sister" in chat, so that I can forget a Thread without opening the Dashboard.
45. As a User turning User Memory off (on the Dashboard or in chat), I want to be told plainly that nothing is deleted and that it just stops learning, so that I understand what off means.
46. As a User, I want to be told Delete My Data removes everything, including private notes I can't see, so that I know how to wipe it all.
47. As a User giving User Memory consent, I want to be told honestly that the Companion also keeps private notes to follow up with me, which Delete My Data removes, so that consent is informed.
48. As a User with User Memory off, I want no new Threads, Portrait updates or Curiosities made, so that off really means stop learning.
49. As a User with User Memory off, I want what's already saved still used, so that the Companion doesn't suddenly forget me.
50. As a User who uses Delete My Data or Account Deletion, I want my Threads, Portrait, Curiosities, Understandings and Model Call Log entries removed, so that nothing about me remains.
51. As a User, I want Message Retention to remove Understandings and log entries with my messages, so that they aren't kept longer than the messages.

### Admins steering the Companion

52. As an Admin, I want to add, edit and delete Needs on the Dashboard with no redeploy, so that humans can steer the core of the product at any time.
53. As an Admin, I want each Need to have a name, "when it fits" and "how to reply", so that I can steer both the pick and the reply.
54. As an Admin, I want one fallback Need that can be edited but never deleted, so that the Companion always has something to fall back on.
55. As an Admin, I want to edit the Understanding prompt and pick its model on the Prompts and Models page, so that I can tune how it reads Users.
56. As an Admin, I want to edit the prompts that write Threads, the Portrait and Curiosities, so that I can tune what the Companion learns.
57. As an Admin, I want to set the closeness bars for Threads, Summaries and Knowledge, so that weak matches don't push forced callbacks.
58. As an Admin, I want to set how many older Summaries and Threads can go into a reply, so that I control cost and focus.
59. As an Admin, I want Curiosities to be a Feature I can switch on or off for everyone or one User, so that it can become a plan extra later.
60. As an Admin, I want to set how many Curiosities are raised per Conversation, how many Curiosity Check-ins a User gets per week, and how many can wait at once, so that I can tune it per future tier.
61. As an Admin, I want to edit the "something I've been wondering" Check-in Kind's wording but not what it does, so that it can't break.
62. As an Admin, I want each Knowledge Document to have a "when it helps" description drafted for me when it's indexed, so that the Companion can reason about which documents fit.
63. As an Admin, I want to edit a document's "when it helps" description, and have replies use it straight away, so that I can steer Knowledge use.
64. As an Admin, I want to edit the fixed lines that explain User Memory off and Delete My Data, so that messaging stays clear and on-voice.
65. As an Admin, I want to see only counts of a User's Threads and whether they have a Portrait, so that Users' lives stay private.

### Admins seeing what happened

66. As an Admin, I want a Model Call Log with one trace per Message or Check-in, so that I can follow everything the Companion did for it.
67. As an Admin, for any User, I want to see which steps ran, the model, tokens, time taken and errors, so that I can spot slow or failing steps.
68. As an Admin, for any User, I want to see the shape of each decision (Need picked, how many Threads found, whether one was raised, which tools were called), so that I can see whether Understanding is working without reading anyone's words.
69. As an Admin, I want never to see a User's words in the log, so that the promise that Admins don't read Users' chats holds.
70. As an Admin, in my own chats with the Companion, I want full content (instructions, history, tools, tool calls and results, the response and the model's reasoning), so that I can debug and tune it.
71. As an Admin, I want Eval runs to keep full content, so that I can see exactly why a case failed.
72. As an Admin, I want an Understanding failure to show in the log while the User still gets a reply, so that failures are visible but harmless.

### Quality and reliability

73. As an Admin, I want an Understanding Eval through the real reply path, so that I know the Companion picks the right Need, is reminded, leaves things alone, doesn't repeat, probes and uses Knowledge only when it fits.
74. As an Admin, I want the Understanding Eval to report its time and tokens, so that I know what it costs on top of a reply.
75. As an Admin, I want the Understanding Eval's cases kept as data files, so that they can move to a future Eval dashboard without a rewrite.
76. As a User, I want a reply even if the Understanding step fails, so that the Companion never goes silent.
77. As a User, I want replies to take about as long as today, so that understanding me doesn't make the Companion slow.
78. As a developer, I want the reply steps in plain core code, so that they're easy to read, test and change.

## Implementation Decisions

### Order of a reply (core, plain Python — ADR-0009)

- A core **ReplyService** runs each Message's reply in a fixed order: house rules (the existing ReplyGate) → being reminded → Understanding → lookups → reply → deliver → save the Understanding. Not an agent loop: the model fills in a form and the code acts on it (option A in the grilling; option B, the reply model driving its own lookups, was rejected for unsteady speed, cost and recall).
- The LangGraph conversation-engine port, its adapter and the Postgres checkpointer (and its tables) are removed; ADR-0003's LangGraph parts are replaced by ADR-0009. This is the first slice, a pure refactor: every existing end-to-end test passes unchanged.
- The design stays open to a later hybrid: one or two lookup tools (e.g. search past Conversations) offered in the reply call's existing tool loop, in the chat model adapter.
- Two model calls per reply, as today: the Understanding call replaces the memory-retrieval (category picking) call.

### Being reminded (no model call)

- On every Message, before the Understanding, the code finds the User's Life Threads by:
  - a direct match on people or things named in the Thread, against the recent User messages;
  - meaning: the last 2–3 User messages joined, embedded and searched against each Thread's story.
- Open Threads rank above settled ones. No age limit. Only matches above an Admin-set closeness bar count, up to an Admin-set number.
- Only the User's own Threads are ever searched.

### The Understanding call

- Inputs: the Understanding prompt (Admin-editable), every Need's name and "when it fits", the User Portrait, Goals, the names of Memory Categories the User has items in, the newest Conversation Summaries, the reminded Threads (with when each was last raised and how the User took it), waiting Curiosities whose "not before" day has come (with the per-Conversation limit and how many were already raised), this Conversation's earlier Understandings, the Knowledge Documents' "when it helps" descriptions, the recent Conversation, and the time and weekday in the User's time zone.
- Output: a fixed-shape form the code parses:
  - `need` (a Need's name), `nuance` (one sentence)
  - `mood`, `intensity` (low / medium / high), `cause_known` (true / false)
  - `memory_categories` (which categories' Memory Items to include; "always include" ones go in regardless)
  - `threads_touched`
  - `bring_up`: items (a Thread, Summary or Curiosity) with how (lead with it / weave it in)
  - `left_alone`: items with a reason
  - `look_up_past`: search phrases for older Summaries (may be empty)
  - `knowledge`: chosen Knowledge Documents and a search phrase (may be empty)
- An unknown Need name or an unreadable form falls back to the fallback Need. A failed call: the reply still goes with the fallback Need, the Portrait, the newest Summaries, "always include" Memory Items and the reminded Threads, and no Knowledge; the failure is logged.
- Model and prompt are Admin settings (start `deepseek-chat`).

### Lookups

- **Older Summaries:** every Conversation Summary is embedded when written. `look_up_past` phrases are searched against the User's own Summaries; matches above a closeness bar, up to an Admin-set number, go into the reply with their dates.
- **Knowledge:** only when the Understanding chose documents. Embeddings find the closest passages *inside those documents only*, above a closeness bar, at most `knowledge_chunks_per_reply`. No more "newest text only" search.

### The reply call

- Gets the Persona and response prompt as today, plus: the picked Need's "how to reply", the nuance, the mood, what to bring up and how, what to leave alone, the User Portrait, the fetched Memory Items, Summaries, Threads, Curiosity and Knowledge. Tools are unchanged.
- The reply is still split into short texts with typing pauses.

### Saved Understanding

- One Understanding per answered Message, linked to it, holding the full form plus when it was made. Removed with its Message by Message Retention, Delete My Data and Account Deletion. The Need is stored by name, so deleting a Need is safe.
- A Curiosity or Thread in `bring_up` is marked raised (with the Conversation) as soon as the reply is sent.

### When a Conversation ends (background, existing post-conversation step)

- The Summary gains a mood arc (from the Conversation's Understandings) and what the Companion offered and how it landed.
- Life Threads: added to or started; each raised Thread records when and how the User took it (engaged / brushed off / asked to drop it); open or settled updated. Embeddings for changed Threads are refreshed.
- User Portrait rewritten from Memory Items, Threads and Summaries.
- Curiosities: new ones written (what to ask and why, "not before" day or anytime, sensitivity), raised ones updated with how the User took them, irrelevant ones closed; the waiting limit drops the oldest.
- None of this runs while User Memory doesn't work for the User (off by them or by an Admin); saved ones are still used.
- Exact split into model calls is an implementation choice; Admin-editable prompts and models for each.

### Data model (new per-User tables, each with delete-for-user, covered by the existing "every per-User table" test)

- **Need** (platform data): name (unique ignoring case), when it fits, how to reply, sort order, is-fallback. Seeded with the six starting Needs; "Ask more" is the fallback.
- **Life Thread**: User, title, story, people or things, open/settled, last updated, last raised at, last reaction, embedding.
- **User Portrait**: one per User, text, updated at.
- **Curiosity**: User, what to ask, why, not-before day, sensitivity, state (waiting / raised with reaction / no longer relevant), source (Memory Item or Thread, for cascading deletes), created at.
- **Understanding**: Message, the form, created at.
- **Conversation Summary**: gains an embedding.
- **Knowledge Document**: gains "when it helps".
- **Model Call Log entry**: trace (Message or Check-in), User, step, model, tokens, duration, error, decision shape; content fields filled only at the full-content level.
- Existing LangGraph checkpoint tables are dropped.

### Model Call Log (ADR-0010)

- Recorded around the existing usage-recording chat model wrapper, so every service is covered without each one logging itself.
- Level is decided per call: full content when the User is an Admin, or when the run is an Eval; content-free otherwise. Local and worktree runs also log full content to developer logs.
- Admin API: list traces (filter by User, date, step, errors), open a trace. Content fields are never returned for non-Admin Users, because they're never stored.

### Curiosities as a Feature and a Check-in Kind

- New Feature **Curiosities** (for everyone and per User, like Personal Stickers). When it doesn't work for a User, none are made, raised or sent; none are deleted.
- Settings: raised per Conversation (start 1), Curiosity Check-ins per week (start 1), waiting at once.
- New fixed-behaviour Check-in Kind "something I've been wondering": wording editable, behaviour not (like the photo Kind). Offered to the Check-in model only for a User with a Curiosity whose day has come, within the weekly limit; sending it marks the Curiosity raised.

### Deleting and privacy

- Deleting a Memory Item or Thread (Dashboard or chat) removes Curiosities sourced from it and queues a Portrait rewrite without it, right away in the background. Deleting the Portrait clears it; it's rebuilt only at a later Conversation end with User Memory working.
- "Forget that" in chat (Settings in Chat) covers Threads too.
- User Memory off: no new Threads, Portrait updates or Curiosities; saved ones used.
- Wording changes (Admin-editable seed text): the consent explanation gets an honest line about private notes; the in-chat User Memory off confirmation includes a fixed line ("Nothing is deleted… use Delete My Data to remove everything"); Delete My Data prompts (chat and Dashboard) mention private notes.

### APIs and Dashboard

- Dashboard API: the User's Portrait and Threads (read, delete).
- Admin API: Needs CRUD (fallback undeletable); the new settings, prompts and models through the existing settings endpoints; the document "when it helps" field through the existing Knowledge document endpoints; Thread and Portrait counts on the User view; Model Call Log list and trace.
- Dashboard pages, following `docs/design/` where they fit: Memories page sections "What I know about you" and "What's going on in your life"; admin Needs page (like Check-in Kinds); admin Model Call Log page; new settings on existing Settings, Prompts and Models and Knowledge pages.

## Testing Decisions

- Good tests check external behaviour only: what the reply call was given, what was sent to the chat, what the APIs return, what deleting removes. Never which internal function ran or how steps are wired.
- **Main seam — the app's outside edges** (Telegram webhook, Dashboard API, Admin API) with real Postgres and the existing fakes, as in the conversation, memory-retrieval, post-conversation, check-in and data-deletion tests:
  - The scripted chat model gains scripts for the Understanding form and the Conversation-end outputs, told apart by instructions as today.
  - The fake embedder (texts sharing words are close) covers reminding by meaning, closeness bars and Knowledge inside chosen documents.
  - The fake clock and timer cover "not before" days, "not raised too soon" and weekly limits.
  - Cases: each Need's guidance reaches the reply; reminded Threads reach the Understanding by name and by meaning, open first, weak ones dropped; `look_up_past` brings old Summaries; Knowledge only when chosen; raised Threads and Curiosities aren't offered again in the Conversation; per-Conversation and weekly Curiosity limits; the fallback on a failed or unreadable Understanding; Conversation-end updates; User Memory off stops learning but keeps using; deletes cascade and rewrite the Portrait; Delete My Data, Account Deletion and Message Retention remove the new data; Model Call Log content level for a plain User vs an Admin; Needs admin rules (fallback undeletable, unique names); the Curiosity Check-in Kind is offered only when a Curiosity is due.
- **Removing LangGraph:** no new tests; the existing end-to-end tests pass unchanged.
- **Evals:** a new Understanding Eval through the real reply path, cases in data files: Need picked (rant, advice, small talk, Goal slip); a rant gets no fixing (Judge); being reminded (sister's wedding raises the old open Thread naturally); leave it alone (same Thread, User struggling); no repeat within a Conversation; brushed off → not raised too soon; strong mood, unknown cause → gentle probe; Curiosity due → raised at most once; Knowledge for a reflective question, not a vent. Reports time and tokens. Existing Persona and Knowledge Evals keep passing.
- **Dashboard:** Vitest + React Testing Library with the API client mocked, as in the existing component tests: Memories page sections and deletes, Needs admin page, Model Call Log page (no content shown for plain Users), new settings fields.
- All language checks pass: `pytest`, `ruff`, `ruff format`, `mypy`; `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`.

## Out of Scope

- **Message grouping** (several texts in a row answered as one Message). Its own issue, built *before* this PRD so Understandings are made per Message from the start. The term is already in `CONTEXT.md`.
- **Keeping typing visible on slow replies** (sending "typing" every ~4 seconds). Its own small issue.
- **Eval dashboard** (run and tune Evals from the Dashboard, draft settings, side-by-side model comparisons). Its own PRD: `.scratch/eval-dashboard/issues/01-run-evals-from-the-dashboard.md`.
- **Trying a stronger reply model.** No code: `deepseek-reasoner` is already selectable; compare with Evals (and later the Eval dashboard).
- **Lookup tools for the reply model** (the hybrid). Kept possible, not built.
- **Searching Memory Items by meaning.** They stay picked by category.
- **Full log content for real Users**, or a User's choice to share a Conversation with the team.
- **Per-plan limits.** Curiosity limits are platform-wide until plans exist.
- **Scaling to several backend processes** (`.scratch/scaling/`).
- **Backfill.** The platform isn't live; the only User is the owner (an Admin), whose data can be reset.
- Anything tagged "Later" in `docs/design/`.

## Further Notes

- Decisions and reasons are in `.scratch/understanding/issues/archive/01-understanding-before-reply.md` (grilled 14 Nov 2026). New terms in `CONTEXT.md`: Message, Life Thread, User Portrait, Need, Understanding, Curiosity, Model Call Log. ADRs: 0009 (replies in plain core code), 0010 (Model Call Log levels).
- Suggested slice order: remove LangGraph (pure refactor) → Model Call Log → Needs and the Understanding call (replacing memory picking) → Summary embeddings and `look_up_past` → Knowledge "when it helps" and scoped search → Life Threads and being reminded → User Portrait → Curiosities (Feature, limits, Check-in Kind) → Dashboard Memories sections and delete cascades → messaging changes → Understanding Eval. Message grouping lands before the Understanding slices.
- Latency: two model calls per reply as today, plus fast local searches. The Understanding call adds a few hundred input tokens (Portrait, descriptions); watch it in the Eval report.
- Being reminded is the heart of this feature; tune its closeness bars and prompt with the Eval before anything else.
