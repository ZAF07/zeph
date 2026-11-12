# AI Companion

A philosophy-informed AI companion that people talk to through Telegram, supported by a web dashboard for accounts, preferences and administration.

## Language

### People

**User**:
A person with an account who converses with the Companion.
_Avoid_: Customer, member, client

**Admin**:
A User who also has access to the admin area of the Dashboard to configure the platform. The first Admins are the Users whose emails are listed as initial Admin emails; after that, Admins make or remove other Admins. There is always at least one Admin: the last one can't be removed.
_Avoid_: Operator, superuser, staff

### Product

**Companion**:
The AI conversational partner a User talks to.
_Avoid_: Bot, assistant, agent

**Persona**:
The Companion's voice and character — human in style, honest that it is an AI. Managed by Admins. Users never pick a style: the Companion adapts to how each User messages.
_Avoid_: System prompt, personality, character

**Sticker Library**:
The Admin-managed set of stickers the Companion may send, at most one per reply. Each has a "when to use" note; a sticker without one is never sent. A sticker an Admin sends the Companion from their own Telegram is added to the library rather than answered. Stickers Users send are read through their emoji.
_Avoid_: Sticker pack, emoji set

**Unsupported Message**:
Something a User sends that the Companion can't read yet, like a voice note or photo. It gets a short in-character reply asking them to type instead; any caption it carries is answered like a message.
_Avoid_: Media message, attachment

**Telegram Connection**:
The link between a User's account and their Telegram account, made once from the Dashboard. A User must have one to talk to the Companion.
_Avoid_: Telegram link, binding, pairing

**Connection Token**:
A one-time, short-lived code from the Dashboard that a User sends to the Companion in Telegram to make their Telegram Connection. It works once, and only for the User who asked for it.
_Avoid_: Link code, invite, pairing code

**Conversation**:
A run of messages between a User and the Companion that ends after a quiet gap (set by an Admin) with no message from either side. Once ended it never reopens: the next message starts a new Conversation. A Check-in the User replies to also starts one.
_Avoid_: Session, thread, chat

**Check-in**:
A message the Companion sends first, unprompted, to a User who has opted in — meant to feel like a friend reaching out, not a task reminder.
_Avoid_: Notification, nudge, reminder, push

**Check-in Kind**:
The style of a Check-in (e.g. casual hello, follow-up on something shared, present-moment prompt), chosen from the User's recent Conversation Summaries and Memory Items. Managed by Admins.
_Avoid_: Template, check-in type

**Dashboard**:
The web app where Users manage their account, preferences and privacy, and where Admins configure the platform.
_Avoid_: Portal, web app, console

**Onboarding**:
The steps a new User completes on the Dashboard before making their Telegram Connection: what the Companion should call them, acknowledging the AI Notice, what brings them here, country and time zone, and User Memory consent. A User who has not finished it cannot use the rest of the Dashboard.
_Avoid_: Setup, registration, sign-up (sign-up is the account creation before it)

**AI Notice**:
The Admin-worded statement that the Companion is an AI, not a therapist, doctor or crisis service, and that Helplines are for emergencies. A User must acknowledge it during Onboarding; a short form stays visible on the Dashboard afterwards.
_Avoid_: Disclaimer, warning, terms

### Safety

**Safeguard**:
The check on every incoming message, read in the light of the Conversation so far, for signs of crisis (suicide or self-harm, danger to others, abuse, medical emergency). Everyday stress or sadness is not a crisis. When the Safeguard can't tell, it treats the message as a crisis: a false alarm is better than a missed crisis.
_Avoid_: Filter, moderation, guardrail

**Crisis Reply**:
The short, warm reply sent instead of a normal one when the Safeguard detects a crisis. It states that the Companion is an AI and points to Helplines for the User's country, or to the International fallback when that country has none. Its wording is set by Admins.
_Avoid_: Emergency message, SOS reply

**Helpline**:
A crisis support contact (name, number, hours) for a given country, managed by Admins. Each country's Helplines are shared in a set order.
_Avoid_: Hotline, resource

**International fallback**:
The one Helpline with no country (e.g. a worldwide helpline directory), shared only with Users whose country has no Helplines. Admins can edit it but never remove it, so every User always has somewhere to turn.
_Avoid_: Default helpline, global helpline

**Safeguard Event**:
A record that the Safeguard detected a crisis for a User: who, when, what kind of risk, and whose Helplines were shared (their country's, or the International fallback). Never includes the message text.
_Avoid_: Alert, incident, flag

### User Memory

**User Memory**:
Everything the Companion has retained about a specific User, made up of Memory Items and Conversation Summaries. The User can turn it off: then nothing new is kept and the Companion doesn't use what it has, but nothing is deleted until the User deletes it.
_Avoid_: Memory, profile, history, context

**Memory Item**:
A single fact about a User (e.g. a goal, value or preference), belonging to one Memory Category. Comes from a Conversation, or from the User's Onboarding answers (their name and what brings them here). Added, updated or removed when a Conversation ends — a changed fact replaces the old one rather than sitting beside it; the User can delete it.
_Avoid_: Memory, fact, note

**Memory Category**:
The kind of fact a Memory Item records, used to fetch only relevant items for each reply. An "always include" category's items go into every reply. Managed by Admins; each has a unique name (ignoring case). Can be archived but never deleted: an archived category keeps its Memory Items, which the User still sees and can delete, but gets no new ones and its items no longer go into replies, even if it is "always include". Restoring it undoes all that.
_Avoid_: Type, tag, label

**Conversation Summary**:
A short account of what one Conversation covered and how the User seemed (its mood), written once, when the Conversation ends. The newest few go into every reply.
_Avoid_: Recap, transcript, log

### Knowledge

**Knowledge**:
The curated library of philosophy, psychology and mindfulness material the Companion draws on, made of Knowledge Documents. Shared by all Users; never about any one User. The Companion brings it in only when it genuinely fits the message, lightly and in its own words, never as a lecture.
_Avoid_: Wisdom base, corpus, content

**Knowledge Document**:
One text in the Knowledge library (text, Markdown or PDF), with a title, a source or author, and a tradition; Admins can change those details at any time and replies use them straight away. It is Pending until it is made ready, then Ready (used in replies) or Failed (with a reason; an Admin can retry it). Only Ready documents are ever used. Its text, read from its file, is what replies draw on; Admins can view and edit it on the document's page, and an edit makes the document Pending until it is re-indexed (it is then marked Edited, as it no longer matches its file word for word). Replacing its file keeps the document, its details and when it was added, reads the new file's text and clears Edited. Deleting one removes it from replies at once.
_Avoid_: File, article, resource

**Starter Knowledge**:
The Knowledge Documents loaded on first run, when the library is empty: public-domain texts and the owner's own summaries, mindfulness first. After that the library is Admin-managed, so a deleted starter document never comes back.
_Avoid_: Default knowledge, seed content

### Web

**Web Search**:
The Companion looking something up on the web while it replies — searching, or reading a page — when the Conversation needs a fact it doesn't know well. Queries carry only the general topic, never the User's personal details, and a reply that uses web information says where it came from. Admins can turn it off for everyone.
_Avoid_: Browsing, internet lookup, googling

**Web Search Limit**:
The most Web Searches the Companion makes for one User in a day, set by Admins; each search and each page read counts as one. The day is the User's own, so it resets at midnight in their time zone. Once it is reached the Companion replies without the web until the next day.
_Avoid_: Search quota, web budget
