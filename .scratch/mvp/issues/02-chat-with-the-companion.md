# 02 — Chat with the Companion

Status: in-progress

## Parent

`.scratch/mvp/PRD.md`

## What to build

A User with a Telegram Connection can chat with the Companion and get replies that feel like texting a friend. Messages go through the LangGraph conversation engine, which calls a response composition service using DeepSeek. The Persona and response prompt are read from platform settings (seeded), never hardcoded. Messages are grouped into Conversations that end after the quiet gap (a setting).

Introduces the chat model port (DeepSeek via LangChain) and the conversation engine port (LangGraph with Postgres checkpointer), keeping graph nodes thin calls into core services (ADR-0003).

## Acceptance criteria

- [ ] A connected User's text message gets a reply from the Companion on Telegram
- [ ] Replies can be split into several short messages, sent with a typing indicator between them
- [ ] The seeded Persona covers: human style (no bullet lists, no "As an AI…", not always ending with a question, light opinions held loosely), honesty (always says it's an AI when asked, never claims a body or life), and gently encouraging real connections over dependency
- [ ] The Companion replies in the language the User writes in
- [ ] Incoming and outgoing messages are saved and attached to a Conversation; a message after the quiet gap starts a new Conversation
- [ ] The current Conversation's earlier messages are included when composing a reply
- [ ] A Telegram user with no Telegram Connection gets a reply pointing them to the Dashboard sign-up
- [ ] Core code imports no LangChain or LangGraph
- [ ] Seam 1 tests with a scripted fake chat model cover: reply sent, multi-message split, Conversation boundary by quiet gap, unknown Telegram user
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`: real conversation on Telegram with DeepSeek

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`
