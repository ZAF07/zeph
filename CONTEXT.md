# AI Companion

A philosophy-informed AI companion that people talk to through Telegram, supported by a web dashboard for accounts, preferences and administration.

## Language

### People

**User**:
A person with an account who converses with the Companion.
_Avoid_: Customer, member, client

**Admin**:
A User who also has access to the admin area of the Dashboard to configure the platform.
_Avoid_: Operator, superuser, staff

### Product

**Companion**:
The AI conversational partner a User talks to.
_Avoid_: Bot, assistant, agent

**Persona**:
The Companion's voice and character — human in style, honest that it is an AI. Managed by Admins. Users never pick a style: the Companion adapts to how each User messages.
_Avoid_: System prompt, personality, character

**Sticker Library**:
The Admin-managed set of stickers the Companion may send, each with a note on when it fits.
_Avoid_: Sticker pack, emoji set

**Telegram Connection**:
The link between a User's account and their Telegram account, made once from the Dashboard. A User must have one to talk to the Companion.
_Avoid_: Telegram link, binding, pairing

**Connection Token**:
A one-time, short-lived code from the Dashboard that a User sends to the Companion in Telegram to make their Telegram Connection. It works once, and only for the User who asked for it.
_Avoid_: Link code, invite, pairing code

**Conversation**:
A run of messages between a User and the Companion that ends after a quiet gap (set by an Admin) with no message from either side. A Check-in the User replies to also starts one.
_Avoid_: Session, thread, chat

**Knowledge**:
The curated library of philosophy, psychology and mindfulness material the Companion draws on. Shared by all Users; never about any one User.
_Avoid_: Wisdom base, corpus, content

**Check-in**:
A message the Companion sends first, unprompted, to a User who has opted in — meant to feel like a friend reaching out, not a task reminder.
_Avoid_: Notification, nudge, reminder, push

**Check-in Kind**:
The style of a Check-in (e.g. casual hello, follow-up on something shared, present-moment prompt), chosen from the User's recent Conversation Summaries and Memory Items. Managed by Admins.
_Avoid_: Template, check-in type

**Dashboard**:
The web app where Users manage their account, preferences and privacy, and where Admins configure the platform.
_Avoid_: Portal, web app, console

### Safety

**Safeguard**:
The check on every incoming message for signs of crisis (suicide or self-harm, danger to others, abuse, medical emergency). Everyday stress or sadness is not a crisis.
_Avoid_: Filter, moderation, guardrail

**Crisis Reply**:
The short, warm reply sent instead of a normal one when the Safeguard detects a crisis. It states that the Companion is an AI and points to Helplines for the User's country.
_Avoid_: Emergency message, SOS reply

**Helpline**:
A crisis support contact (name, number, hours) for a given country, managed by Admins.
_Avoid_: Hotline, resource

**Safeguard Event**:
A record that the Safeguard detected a crisis for a User: who, when and what kind of risk. Never includes the message text.
_Avoid_: Alert, incident, flag

### User Memory

**User Memory**:
Everything the Companion has retained about a specific User, made up of Memory Items and Conversation Summaries.
_Avoid_: Memory, profile, history, context

**Memory Item**:
A single fact about a User (e.g. a goal, value or preference), belonging to one Memory Category. Added, updated or removed when a Conversation ends; the User can delete it.
_Avoid_: Memory, fact, note

**Memory Category**:
The kind of fact a Memory Item records, used to fetch only relevant items. Managed by Admins; can be archived but never deleted.
_Avoid_: Type, tag, label

**Conversation Summary**:
A short account of what one Conversation covered and how the User seemed, written when the Conversation ends.
_Avoid_: Recap, transcript, log
