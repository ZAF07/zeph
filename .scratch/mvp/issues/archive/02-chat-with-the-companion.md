# 02 — Chat with the Companion

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

A User with a Telegram Connection can chat with the Companion and get replies that feel like texting a friend. Messages go through the LangGraph conversation engine, which calls a response composition service using DeepSeek. The Persona and response prompt are read from platform settings (seeded), never hardcoded. Messages are grouped into Conversations that end after the quiet gap (a setting).

Introduces the chat model port (DeepSeek via LangChain) and the conversation engine port (LangGraph with Postgres checkpointer), keeping graph nodes thin calls into core services (ADR-0003).

## Acceptance criteria

- [x] A connected User's text message gets a reply from the Companion on Telegram
- [x] Replies can be split into several short messages, sent with a typing indicator between them
- [x] The seeded Persona covers: human style (no bullet lists, no "As an AI…", not always ending with a question, light opinions held loosely), honesty (always says it's an AI when asked, never claims a body or life), and gently encouraging real connections over dependency
- [x] The Companion replies in the language the User writes in
- [x] Incoming and outgoing messages are saved and attached to a Conversation; a message after the quiet gap starts a new Conversation
- [x] The current Conversation's earlier messages are included when composing a reply
- [x] A Telegram user with no Telegram Connection gets a reply pointing them to the Dashboard sign-up
- [x] Core code imports no LangChain or LangGraph
- [x] Seam 1 tests with a scripted fake chat model cover: reply sent, multi-message split, Conversation boundary by quiet gap, unknown Telegram user
- [x] `make check` passes
- [x] Verified in the running app via `/run`: real conversation on Telegram with DeepSeek

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`

## Comments

**2026-11-11 — implemented on branch `feat/02-chat-with-the-companion`.**

Decisions:
- Ports: `ChatModel.generate(model, instructions, history) -> str` (DeepSeek via `langchain-deepseek`), and `ConversationEngine.handle(turn)` (LangGraph with `PostgresSaver`; one checkpoint thread per User, keyed by User ID). The graph is record_incoming → compose_reply → deliver_reply, and each node is one call into a core service (`ConversationService`, `ResponseComposer`).
- New seeded settings: `persona`, `response_prompt`, `response_model` (`deepseek-chat`), `conversation_quiet_gap_minutes` (60), `unknown_telegram_user_reply`, `reply_failed_message`, `typing_seconds_per_character` (0.05), `min_typing_seconds` (1.5), `max_typing_seconds` (5).
- The model splits its reply into short messages with blank lines. Before each one the Companion shows typing for a pause based on its length (admin settings). Each part is saved right after it is sent.
- The quiet gap is counted from the last message in either direction, so the Companion's reply also keeps a Conversation open.
- Messages are ordered by an auto-increment `position`, because several can share a timestamp.
- The webhook answers Telegram straight away and handles the message in a background task.
- A User's messages are answered one at a time (an in-process lock per User), so a reply always sees the earlier messages.
- If DeepSeek fails or returns nothing, the User gets the seeded `reply_failed_message` and the error is logged.
- `DEEPSEEK_API_KEY` is now required.

Live run feedback, fixed during the issue: replies felt pushy (kept steering back to one topic, nearly always ended with a question) and came too fast. The Persona now says to follow the User's lead, and typing shows before every part.

Caveats / follow-ups:
- The per-User lock works only inside one backend process. Running more than one worker needs a database lock instead.
- The checkpointer is written but never read back (history comes from the database). It's kept for ADR-0003. Data deletion (issue 14) must clear the User's checkpoint thread.
- Telegram's typing indicator lasts about 5 s, so a slow DeepSeek reply can show a gap with no typing.
- The `ChatModel` port returns text only. Tool calls (web search, stickers) will need to extend it.
- Conversations have no `ended_at` / `processed_at` yet; post-conversation processing adds them.
- The seed never overwrites an existing setting, so the updated Persona was written into the local database by hand. Other existing installs keep their old Persona until an Admin edits it.
- Review judgement calls not acted on: the core names `ChatLine`/`history` sit close to CONTEXT.md avoid-words (they follow the PRD's "chat model" port); the `{dashboard_url}` replacement is repeated in two services; `MessageKind` has only `TEXT` so far.

## Completion

- Completed: 2026-11-11
- Commit: a3d4148 (merged from `feat/02-chat-with-the-companion`)
