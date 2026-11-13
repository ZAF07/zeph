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
The Companion's voice and character — human in style, honest that it is an AI. Managed by Admins. In the MVP there is one Persona and Users never pick a style: the Companion adapts to how each User messages. After the MVP there will be several Personas (e.g. mindfulness, Buddhist philosophy, Japanese philosophy), and Users choose one from those their plan includes.
_Avoid_: System prompt, personality, character

**Sticker Library**:
The Admin-managed set of stickers the Companion may send, at most one per reply. Each has a "when to use" note; a sticker without one is never sent. A sticker an Admin sends the Companion from their own Telegram is added to the library rather than answered. Stickers Users send are read through their emoji. Sending stickers is the Stickers Feature: when it doesn't work for a User, the Companion sends them none, but still reads their stickers, and Admins can still add stickers by sending them.
_Avoid_: Sticker pack, emoji set

**Shared Photo**:
A photo a User sent the Companion that matters to them, picked when the Conversation ends and kept as part of their User Memory, with a detailed description written when it arrived and a note on why it matters. Other photos are used only in the Conversation they came in. The Companion works from the description and looks at the photo again only when the description can't answer. It may send a User's own Shared Photo back to them, the way a friend brings up an old memory. It stays after Message Retention deletes the message it came in, until the User deletes it.
_Avoid_: Image, picture, attachment, media

**Photo Viewing**:
A User's choice, on by default, to let the Companion look at the photos they send. When it's off, the Companion doesn't look at their photos or keep them, answers only the caption and says plainly it didn't view the photo; their Shared Photos aren't used but aren't deleted. Every photo is still checked by the Safeguard, whatever this choice, and Users are told so plainly.
_Avoid_: Image recognition, vision, photo mode

**Unsupported Message**:
Something a User sends that the Companion can't read yet, like a voice note or file. It gets a short in-character reply asking them to type instead; any caption it carries is answered like a message.
_Avoid_: Media message, attachment

**Feature**:
An extra the Companion offers that can be switched off: Web Search, Check-ins, User Memory, Photo Viewing, Stickers, Knowledge and Settings in Chat. Admins switch each one on or off for everyone, and for individual Users; a choice for one User overrides the one for everyone. A Feature works for a User only when the Admins allow it and, where the User has their own switch (User Memory, Check-ins), the User has it on. A switch the Admins don't allow shows as "Not available on your account" on the Dashboard and can't be changed; the Admins' choice never changes the User's own. Delete My Data works in chat even when Settings in Chat is off. Safety and a User's rights and privacy are never Features: the Safeguard and Crisis Reply, the AI Notice, Delete My Data and seeing their own data on the Dashboard are always there.
_Avoid_: Capability, add-on, perk, entitlement

**Telegram Connection**:
The link between a User's account and their Telegram account, made once from the Dashboard. A User must have one to talk to the Companion.
_Avoid_: Telegram link, binding, pairing

**Connection Token**:
A one-time, short-lived code from the Dashboard that a User sends to the Companion in Telegram to make their Telegram Connection. It works once, and only for the User who asked for it.
_Avoid_: Link code, invite, pairing code

**Conversation**:
A run of messages between a User and the Companion that ends after a quiet gap (set by an Admin) with no message from either side. Once ended it never reopens: the next message starts a new Conversation. A reply to a Check-in also starts one, beginning with that Check-in.
_Avoid_: Session, thread, chat

**Check-in**:
A message the Companion sends first, unprompted, to a User who has opted in — meant to feel like a friend reaching out, not a task reminder. When the User is due (their frequency gap has passed), not paused, outside their Quiet Hours and not mid-Conversation, the Companion either sends one of a Check-in Kind or skips it. Check-ins are a Feature: when an Admin has them off for a User, none are decided or sent, and the User's own Check-in settings are kept for when they are back on. The User's first message within the reply window (set by an Admin) is its reply; after that it had no reply. Users never see when the next one will come.
_Avoid_: Notification, nudge, reminder, push

**Quiet Hours**:
The local times, in the User's time zone, when the Companion never sends a Check-in. They may run past midnight (e.g. 22:00 until 07:30).
_Avoid_: Do not disturb, sleep hours

**Check-in Pause**:
A break from Check-ins for a day, a week or until the User resumes, which keeps every other Check-in setting. A timed pause ends by itself.
_Avoid_: Snooze, mute

**Check-in Kind**:
The style of a Check-in (e.g. casual hello, follow-up on something shared, present-moment prompt), chosen from the User's recent Conversation Summaries and Memory Items. Managed by Admins; only Kinds marked "allowed without User Memory" go to a User with User Memory off. Users see the Kinds read-only.
_Avoid_: Template, check-in type

**Skipped Check-in**:
A due Check-in the Companion chose not to send, with a reason only Admins see (e.g. the User asked for space). The next attempt waits a full frequency gap, as after a sent one. Users see it only as "gave you some space".
_Avoid_: Cancelled, missed, failed check-in

**Ignore Threshold**:
The Admin-set number of sent Check-ins in a row with no reply after which the Companion sends one "would you like fewer?" message and puts the User on a Check-in Pause until they resume. Any message from the User starts the count again.
_Avoid_: Ignore limit, unanswered cap

**Check-in Log**:
The Admins' record of every Check-in decision — sent with its Kind, skipped with its reason, or paused by the Ignore Threshold — and whether the User replied. Never the message text.
_Avoid_: Check-in history (that is the User's own "Recent check-ins")

**Dashboard**:
The web app where Users manage their account, preferences and privacy, and where Admins configure the platform.
_Avoid_: Portal, web app, console

**Chat Setting Change**:
A change to one of a User's settings made by telling the Companion in plain words instead of on the Dashboard: pausing or resuming Check-ins, Check-in frequency, quiet hours, User Memory on or off, time zone, forgetting a Memory Item, or Delete My Data. The Dashboard marks each such setting "Changed in chat" until it is next changed there.
_Avoid_: Chat command, slash command, bot setting

**Onboarding**:
The steps a new User completes on the Dashboard before making their Telegram Connection: what the Companion should call them, acknowledging the AI Notice, what brings them here, country and time zone, and User Memory consent. A User who has not finished it cannot use the rest of the Dashboard.
_Avoid_: Setup, registration, sign-up (sign-up is the account creation before it)

**AI Notice**:
The Admin-worded statement that the Companion is an AI, not a therapist, doctor or crisis service, and that Helplines are for emergencies. A User must acknowledge it during Onboarding; a short form stays visible on the Dashboard afterwards.
_Avoid_: Disclaimer, warning, terms

### Safety

**Safeguard**:
The check on every incoming message, photos included, read in the light of the Conversation so far, for signs of crisis (suicide or self-harm, danger to others, abuse, medical emergency). Everyday stress or sadness is not a crisis. When the Safeguard can't tell, it treats the message as a crisis: a false alarm is better than a missed crisis.
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
Everything the Companion has retained about a specific User, made up of Memory Items, Conversation Summaries and Shared Photos. The User can turn it off: then nothing new is kept and the Companion doesn't use what it has, but nothing is deleted until the User deletes it. It is also a Feature: an Admin turning it off for a User has exactly the same effect, keeps the User's own choice for when it is back on, and still lets the User see and delete their memories.
_Avoid_: Memory, profile, history, context

**Memory Item**:
A single fact about a User (e.g. a goal, value or preference), belonging to one Memory Category. Comes from a Conversation, or from the User's Onboarding answers (their name and what brings them here). Added, updated or removed when a Conversation ends — a changed fact replaces the old one rather than sitting beside it; the User can delete it.
_Avoid_: Memory, fact, note

**Memory Category**:
The kind of fact a Memory Item records, used to fetch only relevant items for each reply. An "always include" category's items go into every reply. Managed by Admins; each has a unique name (ignoring case). Can be archived but never deleted: an archived category keeps its Memory Items, which the User still sees and can delete, but gets no new ones and its items no longer go into replies, even if it is "always include". Restoring it undoes all that. One category (Goals, to start) holds a User's goals; the Dashboard shows its items as what the User is working toward, and renaming it keeps that link.
_Avoid_: Type, tag, label

**Conversation Summary**:
A short account of what one Conversation covered and how the User seemed (its mood), written once, when the Conversation ends. The newest few go into every reply.
_Avoid_: Recap, transcript, log

### Knowledge

**Knowledge**:
The curated library of philosophy, psychology and mindfulness material the Companion draws on, made of Knowledge Documents. Shared by all Users; never about any one User. The Companion brings it in only when it genuinely fits the message, lightly and in its own words, never as a lecture. It is a Feature: when it doesn't work for a User, no Knowledge goes into their replies.
_Avoid_: Wisdom base, corpus, content

**Knowledge Document**:
One text in the Knowledge library (text, Markdown or PDF), with a title, a source or author, and a tradition; Admins can change those details at any time and replies use them straight away. It is Pending until it is made ready, then Ready (used in replies) or Failed (with a reason; an Admin can retry it). Only Ready documents are ever used. Its text, read from its file, is what replies draw on; Admins can view and edit it on the document's page, and an edit makes the document Pending until it is re-indexed (it is then marked Edited, as it no longer matches its file word for word). Replacing its file keeps the document, its details and when it was added, reads the new file's text and clears Edited. Deleting one removes it from replies at once.
_Avoid_: File, article, resource

**Starter Knowledge**:
The Knowledge Documents loaded on first run, when the library is empty: public-domain texts and the owner's own summaries, mindfulness first. After that the library is Admin-managed, so a deleted starter document never comes back.
_Avoid_: Default knowledge, seed content

### Web

**Web Search**:
The Companion looking something up on the web while it replies — searching, or reading a page — when the Conversation needs a fact it doesn't know well. Queries carry only the general topic, never the User's personal details, and a reply that uses web information says where it came from. It is a Feature, so Admins can turn it off; when it doesn't work for a User, the Companion tells them plainly it isn't available on their account.
_Avoid_: Browsing, internet lookup, googling

**Web Search Limit**:
The most Web Searches the Companion makes for one User in a day, set by Admins; each search and each page read counts as one. The day is the User's own, so it resets at midnight in their time zone. Once it is reached the Companion replies without the web until the next day.
_Avoid_: Search quota, web budget

### Usage

**Daily Message Limit**:
The most messages a User can send the Companion in a day, set by Admins and meant to be generous. The day is the User's own, so it resets at midnight in their time zone. The Safeguard still checks every message first: a crisis always gets the Crisis Reply and never counts toward the limit. Over the limit, the Companion answers with the Limit Reply instead of a real reply until the next day.
_Avoid_: Quota, rate limit, message cap

**Limit Reply**:
The short, in-character message (e.g. "I'm wiped for today, talk tomorrow?") sent instead of a reply once a User is over the Daily Message Limit. Its wording is set by Admins.
_Avoid_: Error message, limit notice

**Usage**:
What each User used on each of their days, as counts only: messages, chat model tokens read and written (for everything the Companion does for them, Check-ins included), and Web Searches, plus whether the Daily Message Limit or Web Search Limit turned anything away that day. Admins see it; it never holds message content.
_Avoid_: Billing, costs, activity log

### Privacy

**Message Retention**:
How long a User's raw messages are kept, set by Admins in days. Older messages are deleted automatically; Conversation Summaries and Memory Items stay until the User deletes them.
_Avoid_: Data retention, TTL, history limit

**Delete My Data**:
A User's choice, on the Dashboard or in chat, to wipe their messages, User Memory, Check-in history and Telegram Connection after typing a confirmation word. In chat the confirmation must be their whole next message; anything else cancels it. Their account stays, so they can start fresh. The Admins' Feature choices for them stay too, since they are Admin settings, not the User's data.
_Avoid_: Reset, clear history, wipe

**Account Deletion**:
A User's choice, made only on the Dashboard, to remove everything Delete My Data removes plus their account itself and the Admins' Feature choices for them. It can't be undone, and the last Admin can't do it.
_Avoid_: Close account, deactivate, unsubscribe

### Quality

**Eval**:
A measurement of how the Companion behaves with the real LLM, run on demand (`make eval`) and never in the normal checks, because it costs money and its results vary. There are Safeguard, Persona, Knowledge and Settings Evals; a Settings Eval checks that plain-words requests make exactly the right Chat Setting Change, or none. Each one goes through the real reply path and uses the platform settings Admins have set.
_Avoid_: Test, benchmark

**Missed Crisis**:
A real crisis that the Safeguard lets through as "none". Any Missed Crisis fails the Safeguard Eval.
_Avoid_: False negative

**False Alarm**:
An everyday message that the Safeguard treats as a crisis, such as "this traffic is killing me". False Alarms are reported but are accepted in small numbers.
_Avoid_: False positive

**Judge**:
The LLM that marks a Persona or Knowledge Eval: for each Persona rule it says whether the replies keep it, and for a Knowledge Eval it says which version of a document a reply used. It always gives a reason. It can be wrong.
_Avoid_: Grader, evaluator
