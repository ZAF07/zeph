# 01 — Understanding: the Companion works out what the User needs before replying

Status: needs-triage

## Idea (from the User, during the architecture grilling, 14 Nov 2026)

Chatting with the Companion still feels slightly empty. Today it goes straight from "here is everything" to one reply call. It should first try to understand the User and their intent, then decide its next step:

- Should it ask more to understand?
- Does it have memories about the User that make the reply meaningful?
- Is this something the User keeps coming back to, and what worked for them before?
- Is any Knowledge relevant, and should the Companion bring it up?
- Or does the User simply want to rant?

The Companion is not just a chat companion. It helps Users understand themselves, acts as an accountability partner for their intentions, goals and ambitions, and helps them make sense of their life. Think life coach, therapist, accountability partner and close friend who knows them well.

## What we noticed in the code

- No thinking step: `ResponseComposer.compose` is one model call (with tools).
- Memory is picked by Memory Category, before the Companion understands the message.
- Knowledge search embeds only the newest message.
- Nothing looks for patterns across Conversations.

## Next

Grill with `/grill-with-docs`, then `/to-prd`. This also settles whether LangGraph stays (see `.scratch/architecture/issues/01-reply-gate.md`).
