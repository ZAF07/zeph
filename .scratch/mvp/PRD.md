# PRD: AI Companion MVP

Status: ready-for-agent

## Problem Statement

People who care about mindfulness, self-understanding and living deliberately struggle to turn what they know into everyday practice. Self-help content is passive, journaling and meditation apps wait for the person to start, and generic AI assistants feel like tools: they forget past conversations, answer like a search engine and never reach out first.

For this MVP, the immediate problem is the owner's: they need a working, real-product-quality Companion that a small group of family and friends in Singapore can use day to day, so they can learn whether people find it valuable and keep coming back — before investing in payments, tiers or a public launch.

## Solution

A Companion that Users talk to on Telegram as if texting a thoughtful friend. It remembers what matters about each User (User Memory), draws on a curated library of mindfulness teachings (Knowledge), can look things up on the web, sends the occasional sticker, and — if the User opts in — reaches out first with Check-ins that feel like a friend saying hello, not a task reminder. It is human in style but always honest that it is an AI, and a Safeguard on every message makes sure anyone in crisis is pointed to real Helplines for their country.

A web Dashboard lets Users sign up, go through onboarding (AI notice, User Memory consent, country and time zone, Check-in preferences), make their Telegram Connection, and view or delete what the Companion remembers. Admins use the Dashboard's admin area to configure everything about the platform — Persona, prompts, Helplines, Knowledge, Memory Categories, Check-in Kinds, Sticker Library, limits and models — without code changes.

Every external dependency sits behind a port so it can be swapped by config: DeepSeek (LLM), LangGraph (orchestration), Clerk (auth), Postgres + pgvector (storage), fastembed (embeddings), Tavily (web search) and Telegram (chat channel).

## User Stories

### Sign-up and onboarding

1. As a new User, I want to sign up on the Dashboard with Clerk (email or social login), so that I can get an account without another password to manage.
2. As a new User, I want to be told clearly that the Companion is an AI and not therapy or medical care, so that I understand what I am talking to.
3. As a new User, I want to confirm "I understand" on the AI notice before continuing, so that the platform knows I have seen it.
4. As a new User, I want a plain-language explanation of what User Memory remembers and how I can delete it, so that I can give informed consent.
5. As a new User, I want User Memory to be on by default with a clear toggle to turn it off, so that I get a personal experience but stay in control.
6. As a new User, I want to set my country, so that I am shown the right Helplines if I ever need them.
7. As a new User, I want to set my time zone, so that Check-ins and quiet hours happen at sensible local times.
8. As a new User, I want to choose whether to turn on Check-ins during onboarding (off by default), so that the Companion only messages me first if I want it to.
9. As a new User turning on Check-ins, I want to pick a frequency and quiet hours, so that messages fit my life.
10. As a new User, I want a "Connect Telegram" button that opens the Companion in Telegram with a one-time link, so that my Telegram account is joined to my Dashboard account in one tap.
11. As a new User, I want the Companion to send me a warm first message as soon as my Telegram Connection is made, so that I am not left staring at an empty chat.
12. As a new User, I want an expired or already-used connection link to fail clearly and let me get a new one from the Dashboard, so that I am never stuck.
13. As a User, I want my Telegram Connection to belong to only one account at a time, so that nobody else's messages end up in my User Memory.

### Conversation

14. As a User, I want to chat freely with the Companion on Telegram about everyday life, feelings, relationships, goals and big questions, so that I have a thoughtful partner to reflect with.
15. As a User, I want the Companion to talk like a friend — short, uneven messages, sometimes split over two or three texts with a typing indicator — so that it does not feel like a chatbot.
16. As a User, I do not want bullet lists, "Great question!", "As an AI…" or a question at the end of every message, so that the conversation feels natural.
17. As a User, I want the Companion to have light, loosely held opinions, so that it feels like a real conversation partner while I still make my own decisions.
18. As a User, I want the Companion to refer casually to things we have talked about before, so that it feels like it knows me.
19. As a User, I want the Companion to bring in mindfulness or philosophical ideas only when they genuinely fit, without lecturing, so that I gain perspective without being preached at.
20. As a User, I want the Companion to reply in the language I write in, so that I can talk the way I normally do.
21. As a User, when I ask "are you a real person?", I want an honest, warm answer that it is an AI, so that I am never deceived.
22. As a User, I want the Companion never to claim a body, a life or experiences it did not have, so that its friendliness stays honest.
23. As a User who seems to be relying on the Companion instead of people in my life, I want it to gently encourage those real connections, so that it supports my wellbeing rather than dependency.
24. As a User, I want a Conversation to continue naturally while I keep replying, and to be treated as finished after a quiet gap, so that the Companion processes it at a sensible moment.
25. As a User, when I reply to a Check-in, I want that to start a normal Conversation, so that a Check-in can lead to a real chat.

### Settings via chat

86. As a User, I want to change my settings by telling the Companion in plain words (pause or resume Check-ins, change frequency or quiet hours, turn User Memory on or off, forget a specific memory, change time zone), so that I don't have to leave the chat (ADR-0006).
87. As a User, I want the Companion to tell me plainly what it changed, and the Dashboard to show the same thing, so that I always know my real settings.
88. As a User, I want to ask for "Delete my data" in chat, but only have it happen after I reply with an exact confirmation word, so that a misunderstanding never wipes my data.
89. As a User, I want Delete account, country and disconnecting Telegram to stay on the Dashboard only, so that permanent or safety-related changes are never made by mistake.

### Dashboard (from the web UI design review)

90. As a new User, I want to tell the Companion what to call me and what brings me here during onboarding, so that our first Conversation starts in the right place.
91. As a User, I want to see my Conversation Summaries (what we talked about and how I seemed) and delete any of them, so that every part of User Memory is visible and in my control.
92. As a User, I want to delete all my Memory Items at once, so that I can start fresh without deleting everything else.
93. As a User, I want to pause Check-ins for a day, a week or until I resume, without losing my settings, so that I can have quiet when I need it.
94. As a User, I want to see my recent Check-ins (sent, replied, skipped to give me space), but never a promised next time, so that I know what's happening without feeling scheduled.
95. As a User, I want a "Delete account" option that removes all my data and my account, so that I can leave completely.
96. As a User, I want a home page showing my Telegram Connection, Check-in status, my goals and what was recently remembered, so that I can see where things stand at a glance.

### Stickers and message types

26. As a User, I want the Companion to occasionally send a fitting sticker, so that our chat feels like texting a friend.
27. As a User, I want the Companion to understand the stickers I send (through their emoji), so that I can reply the way I would to a friend.
28. As a User sending a voice note or photo, I want an in-character reply that it can't handle those yet and to type instead, so that I know what works.
29. As a User in crisis, I do not want a sticker in the Crisis Reply, so that the moment is treated seriously.

### Web search

30. As a User, I want the Companion to look things up on the web when the conversation needs it (e.g. a quote, a book, a fact), so that its answers are current and accurate.
31. As a User, I want the Companion to mention where web information came from, so that I can judge it myself.
32. As a User, I want web search queries never to include my personal details, so that my private life is not sent to a search provider.

### Safeguard

33. As a User in crisis (suicide or self-harm, danger to others, abuse, medical emergency), I want a short, warm Crisis Reply with Helplines for my country, so that I can reach real help quickly.
34. As a User in crisis, I want the Crisis Reply to say plainly that the Companion is an AI and not a replacement for real help, so that I know to reach out to people who can help.
35. As a User whose country has no Helplines set up, I want an international fallback (e.g. a helpline directory), so that I still get somewhere to turn.
36. As a User having a hard day (stress, sadness), I want the Companion to respond normally and kindly rather than treating me as a crisis, so that I am not alarmed or brushed off.
37. As a User, I want the Safeguard to run even if I have hit my daily message limit, so that a crisis is never met with "talk tomorrow".
38. As a User, I want Admins to see only that a Safeguard Event happened (who, when, what kind of risk), never my message text, so that my privacy is protected.

### User Memory

39. As a User, I want the Companion to remember meaningful facts about me as Memory Items, so that I don't have to repeat myself.
40. As a User, I want the Companion to keep a short Conversation Summary of each Conversation, including how I seemed, so that it can pick up where we left off.
41. As a User, I want Memory Items to be updated or removed when things change (e.g. I changed jobs), rather than piling up as contradictions, so that what it remembers stays accurate.
42. As a User, I want the Companion to use only the Memory Items relevant to what I am talking about, so that its replies stay focused.
43. As a User, I want to see all my Memory Items on the Dashboard, grouped by Memory Category, so that I know what the Companion remembers.
44. As a User, I want to delete any single Memory Item, so that I control what is remembered.
45. As a User, I want to turn User Memory off at any time, so that no new Memory Items or Conversation Summaries are saved from then on.
46. As a User with User Memory off, I want the Companion to still work for conversation, so that I am not forced to share in order to use it.
47. As a User, I want a "Delete my data" option that removes my messages, User Memory, Check-in history and Telegram Connection, so that I can leave cleanly.
48. As a User, I want raw messages to be deleted automatically after a retention period, so that my full chat history is not kept forever.

### Knowledge

49. As a User, I want the Companion to draw on curated mindfulness teachings when relevant, so that its reflections are grounded in real traditions.
50. As a User, I want the Companion to ignore Knowledge that does not genuinely fit my message, so that it doesn't force quotes into the conversation.

### Check-ins

51. As a User with Check-ins on, I want the Companion to message me first now and then, so that it feels like a friend who thinks of me.
52. As a User, I want Check-ins to vary — sometimes just "hey, how are you?", sometimes a follow-up on something I shared, a present-moment prompt or a thought to reflect on — so that they feel natural, not scripted.
53. As a User, I want the kind of Check-in chosen from how I've been recently (my Conversation Summaries and Memory Items), so that it fits where I am right now.
54. As a User going through something hard, I want the Companion to sometimes decide not to message me, so that it doesn't intrude when I need space.
55. As a User, I want no Check-ins during my quiet hours, so that I am not disturbed at night.
56. As a User, I want to change my Check-in frequency and quiet hours, or turn Check-ins off, from the Dashboard at any time.
57. As a User who has ignored several Check-ins in a row, I want the Companion to pause and ask once whether I'd like fewer, so that it is never pushy.
58. As a User with User Memory off, I want Check-ins (if on) to only be casual hellos, so that they don't pretend to remember things.

### Usage limits

59. As a User, I want a generous daily message limit, and an in-character message when I reach it, so that the limit feels friendly rather than like an error.

### Admin: access

60. As the owner, I want my account to become an Admin automatically when I sign up with an email listed in config, so that I can get into the admin area from day one.
61. As an Admin, I want to promote or demote other Users to Admin, so that I can share the work.
62. As an Admin, I want to be prevented from demoting the last Admin, so that nobody gets locked out.
63. As a non-Admin, I want admin pages and admin API calls to be refused by the backend, not just hidden, so that the platform is secure.

### Admin: configuration

64. As an Admin, I want to edit the Persona (voice, character and honesty rules), so that I can tune how the Companion feels without a deploy.
65. As an Admin, I want to edit the prompts used by each core service (Safeguard, Response Composition, post-conversation processing, Check-ins), so that I can improve behaviour without code changes.
66. As an Admin, I want to choose which model each core service uses, so that I can balance cost and quality (e.g. a cheaper model for the Safeguard).
67. As an Admin, I want to edit the Crisis Reply wording, so that it reads right for our Users.
68. As an Admin, I want to add, edit and remove Helplines per country, plus an international fallback, so that Users anywhere get the right help.
69. As an Admin, I want to add, rename, describe, archive and restore Memory Categories, and mark some as "always include", so that User Memory is organised the way we need.
70. As an Admin, I want archived Memory Categories to keep their existing Memory Items but not receive new ones, so that nothing is lost.
71. As an Admin, I want to manage Check-in Kinds (name and description the LLM uses to choose), so that I can shape how the Companion reaches out.
72. As an Admin, I want to add stickers to the Sticker Library (by sending them to the Companion from my admin Telegram account, or by sticker set name) with a "when to use" note, so that the Companion has stickers to send.
73. As an Admin, I want to remove stickers from the Sticker Library, so that unsuitable ones are no longer sent.
74. As an Admin, I want to upload Knowledge documents (text, Markdown, PDF) with title, source/author and tradition, so that the Companion can draw on them.
75. As an Admin, I want to see each Knowledge document's processing status and delete documents, so that I can manage the library.
76. As an Admin, I want to set the Conversation quiet gap, daily message limit, Check-in ignore threshold, raw message retention days, web search on/off and per-User daily web search limit, so that I can run the platform without code changes.

### Admin: oversight

77. As an Admin, I want to see a list of Users with their signup date, Telegram Connection status and activity counts (never message content), so that I know how the test is going.
78. As an Admin, I want to see Safeguard Events, so that I know whether crises are happening and how often.
79. As an Admin, I want to see Check-in sends and skips with the skip reason (never message content), so that I can tell whether Check-ins are working well.
80. As an Admin, I want to see token usage per User per day, so that I understand costs and can set future pricing.

### Owner / developer

81. As the developer, I want every external dependency behind a port with the adapter chosen in `.env`, so that I can swap providers without touching core logic.
82. As the developer, I want the same Docker Compose setup to run locally and in production, so that what I test is what ships.
83. As the developer, I want Telegram to use a webhook locally (through ngrok) as well as in production, so that the local path matches production.
84. As the developer, I want platform content to be loaded from seed data files on first run (e.g. Singapore Helplines, starter Memory Categories, Check-in Kinds, starter Persona), so that nothing is hardcoded but a fresh install works.
85. As the developer, I want an eval suite with a README, run separately from the normal checks, so that I can measure Safeguard detection and Persona quality when I change prompts or models.

## Implementation Decisions

See `CONTEXT.md` for terms and ADR-0001 to ADR-0005 for the architectural decisions this PRD relies on.

### Architecture

- A single Python FastAPI backend service hosts: the Telegram webhook, the Dashboard API, and the in-process scheduler loop (ADR-0002).
- The Dashboard is a separate Next.js (TypeScript, App Router) app holding no business logic; it calls the Dashboard API through one API client (ADR-0002, CLAUDE.md).
- Ports and adapters throughout (ADR-0003). The core never imports LangChain, LangGraph, Clerk, Telegram, Tavily or database libraries.
- LangGraph orchestrates the steps of handling a message, but each graph node is a thin call into a core service. Business logic lives only in the services (ADR-0003).
- All platform content and tunable settings are admin-managed data in the database; `.env` holds only secrets, adapter selection and initial Admin emails (ADR-0004).
- Everything runs in Docker Compose (backend, Dashboard, Postgres with pgvector), identical locally and in production; Caddy terminates HTTPS in production; ngrok tunnels the webhook locally (ADR-0005).

### Ports (core-owned interfaces) and MVP adapters

- **Chat model** — generate text and tool calls from a prompt and messages, with the model name passed per call. Adapter: DeepSeek via LangChain's chat-model interface.
- **Conversation engine** — given an incoming message for a User, produce the outgoing messages. Adapter: LangGraph graph with Postgres checkpointer.
- **Chat channel** — send text (optionally split into several messages with typing indicator), send a sticker, and translate incoming updates (text, sticker emoji, unsupported types) into a channel-neutral incoming message. Adapter: Telegram.
- **Auth verifier** — turn a Dashboard request token into an account identity. Adapter: Clerk JWT verification.
- **Repositories** — persistence for each aggregate (Users, Conversations, messages, User Memory, Knowledge, settings, etc.). Adapter: Postgres.
- **Vector store** — store and search Knowledge chunk embeddings. Adapter: pgvector.
- **Embedder** — turn text into embeddings. Adapter: fastembed with a small local BGE model.
- **Web search** — search and fetch page content. Adapter: Tavily.
- **Scheduler** — run due work on a tick. Adapter: in-process loop every few minutes.
- **Clock** — current time, so time-driven behaviour is testable.

### Core services

- **Safeguard** — classifies each incoming message for crisis risk (suicide or self-harm, danger to others, abuse, medical emergency, or none). On crisis: the graph branches to the Crisis Reply (Admin-edited wording plus Helplines for the User's country, else the international fallback), records a Safeguard Event without message text, and skips normal response composition. Runs before the daily limit check.
- **Usage limiter** — enforces the per-User daily message limit and web search limit; records token usage per User per day.
- **Memory retrieval** — picks relevant Memory Categories for the incoming message with a cheap LLM call, then loads Memory Items from those categories plus all "always include" categories, plus the last few Conversation Summaries. No vector search over User Memory.
- **Knowledge retrieval** — embeds the incoming message and fetches the top few matching Knowledge chunks.
- **Response composition** — builds the prompt from Persona, User Memory, Knowledge and the current Conversation; may call tools: web search, page fetch, and pick a sticker from the Sticker Library. Output is one or more short text messages plus an optional sticker.
- **Post-conversation processing** — when a Conversation ends (quiet gap elapsed, detected on scheduler tick), one LLM call produces a Conversation Summary (topics and how the User seemed) and a list of add/update/remove operations against the User's existing Memory Items, each assigned to an active Memory Category. Skipped entirely when User Memory is off.
- **Check-in service** — on scheduler tick, finds Users due a Check-in (opted in, frequency elapsed, outside quiet hours in their time zone, not paused). Reads recent Conversation Summaries and Memory Items, then decides: a Check-in Kind and message, or skip with a reason. Skips push the next attempt to the following slot. After the Admin-set number of consecutive ignored Check-ins, sends one "would you like fewer?" message and pauses. With User Memory off, only the casual-hello kind is allowed.
- **Telegram Connection** — issues a one-time, expiring connection token for a User; the Telegram `/start <token>` message consumes it, links the Telegram user ID to the account, and triggers the welcome message. A Telegram account can be linked to only one User.
- **Admin bootstrap and roles** — on first sign-in, a User whose email is in the initial Admin emails config gets the Admin role. Role is stored in our database, not Clerk. The last Admin cannot be demoted.
- **Retention cleanup** — on scheduler tick, deletes raw messages older than the retention setting.
- **Data deletion** — "Delete my data" removes the User's messages, User Memory, Check-in history and Telegram Connection (and LangGraph checkpoints for that User).
- **Knowledge ingestion** — on upload, extract text (text, Markdown, PDF), split into chunks, embed, store; document status moves through pending → ready / failed.
- **Seeding** — on first run, loads seed data files: Singapore Helplines and international fallback, starter Memory Categories (Life details, Relationships, Goals, Values & beliefs, Challenges, Preferences, What helps — Values & beliefs, Challenges and Preferences are "always include"), starter Check-in Kinds (casual hello, follow-up, present-moment prompt, thought to reflect on), starter Persona, prompts and settings defaults. Starter Knowledge is mindfulness-focused, public-domain texts plus the owner's own summaries.

### Message handling flow (the graph)

1. Incoming update → channel-neutral incoming message. Unknown Telegram user (no Telegram Connection) → reply pointing to the Dashboard sign-up. Unsupported type (voice, photo) → in-character "can't do that yet" reply.
2. Save message; attach to the open Conversation or start a new one.
3. Safeguard → on crisis, Crisis Reply and stop.
4. Usage limiter → over limit, in-character "talk tomorrow" message and stop.
5. Memory retrieval and Knowledge retrieval.
6. Response composition (with optional tools).
7. Send via chat channel; save outgoing messages; record token usage.

### Schema (main tables, described not prescribed)

- Users: Clerk ID, email, name, onboarding reasons ("What brings you here?"), role, country, time zone, AI-notice acknowledged at, User Memory enabled, Check-in settings (enabled, frequency, quiet hours, paused until, consecutive ignored count, next due at), onboarding completed at.
- Telegram Connections: User, Telegram user ID (unique), Telegram chat ID, connected at. Connection tokens: User, token, expires at, used at.
- Conversations: User, started at, last message at, ended at, processed at.
- Messages: Conversation, direction, kind (text, sticker, unsupported), content, sent at.
- Conversation Summaries: Conversation, User, summary, mood, created at.
- Memory Categories: name, description, always include, archived.
- Memory Items: User, Memory Category, content, created at, updated at, source Conversation.
- Knowledge documents: title, source/author, tradition, status. Knowledge chunks: document, text, embedding.
- Helplines: country (or international), name, number, hours, sort order.
- Safeguard Events: User, risk type, created at.
- Check-ins: User, Check-in Kind (or skipped), skip reason, sent at, replied at.
- Check-in Kinds: name, description, allowed without User Memory.
- Sticker Library: Telegram file ID, emoji, "when to use" note, active.
- Platform settings: key/value with types (quiet gap, limits, retention days, web search toggle, model per service, Persona, prompts, Crisis Reply wording).
- Usage: User, date, message count, web search count, tokens in, tokens out.

### API contracts (Dashboard API, all JSON, all authenticated via the auth verifier)

- **User:** get/update own profile and onboarding fields; acknowledge AI notice; set User Memory on/off; get/update Check-in settings; create a Telegram connection link; get Telegram Connection status; list own Memory Items by Memory Category; delete a Memory Item; delete all own data.
- **Admin (role checked on every call):** list Users with counts; change a User's role; CRUD for Helplines, Check-in Kinds, Sticker Library; create, edit, archive and restore Memory Categories; upload, list, retry (failed only) and delete Knowledge documents; get/update platform settings (Persona, prompts, models, Crisis Reply, limits, toggles); list Safeguard Events; list Check-in sends/skips; view usage per User per day.
- **Telegram webhook:** receives updates; verified with Telegram's secret token header.

## Testing Decisions

- **Good tests check behaviour from the outside, not implementation details.** They send a request or tick the scheduler, then check what was sent to the User, what was saved, or what the API returned. They don't check which internal function was called. Restructuring inside the backend must not break tests.
- **Seam 1 — backend HTTP surface (main seam).** Tests drive the Telegram webhook endpoint and the Dashboard API through FastAPI's test client. External services use fake adapters: a scripted fake chat model, a recording fake chat channel, fake web search, fake embedder, fake auth verifier and fake clock. Postgres is real (throwaway test container). This covers conversation, Safeguard, User Memory retrieval, Knowledge retrieval, stickers, limits, onboarding, Telegram Connection, Admin roles and Admin configuration.
- **Seam 2 — scheduler tick with a fake clock.** Tests call the scheduler tick directly at chosen times to cover Conversation ending and post-conversation processing, Check-ins (send, skip, quiet hours, ignore-pause, User Memory off) and retention cleanup.
- **Seam 3 — Dashboard.** Vitest and React Testing Library on pages and components, with the API client mocked.
- **Seam 4 — evals (`make eval`).** Real LLM, separate from normal checks because it costs money and results vary. Safeguard evals (~30 labelled messages: clear crises, subtle crises, false alarms; the target is that every real crisis is caught) and Persona evals (scripted conversations judged by an LLM against the Persona rules). Ships with a README explaining how to run it and read the results.
- Each adapter gets a small contract test against its real service, run separately (not in the fast loop) because it needs network and keys.
- **Prior art:** none — this is a greenfield repo. The first issue sets up the patterns (test container fixture, fake adapters, test client) that the rest follow.

## Out of Scope

- Subscriptions, payments, free/paid tiers
- Sending or receiving photos; voice notes (speech-to-text)
- Google Calendar integration
- Guided reflection journeys and progress tracking
- Channels other than Telegram
- Waitlists, invite codes or approval for sign-up (sign-up is open; the platform won't be marketed)
- Automatic contact with anyone during a crisis
- Vector search over User Memory
- Admins reading Users' message content
- A managed job queue (the in-process scheduler is enough for the MVP)

## Further Notes

- **Before testers start:** the owner must verify the seeded Singapore Helplines (SOS 1767, IMH Mental Health Helpline 6389 2222, emergency 995).
- **Repo setup:** the project is not a git repository yet; `git init` is needed before work starts on a branch.
- **Local dev:** needs an ngrok account; a fixed ngrok domain keeps the webhook URL stable.
- **Copyright:** Knowledge seed content is limited to public-domain texts and the owner's own summaries; modern teachers' works only as the owner's own summaries.
- **Check commands:** CLAUDE.md lists the checks for each language; the first issue should add a `make check` that runs them all, plus `make eval`.
- **Honesty boundary:** "human in style, honest about what it is" is a core product principle — any Persona change must keep the honesty rules intact, and the Persona evals guard this.
