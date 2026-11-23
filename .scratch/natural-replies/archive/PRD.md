# PRD: Natural replies: Zeph answers when the User seems done, and sees what they reply to

Status: completed

## Problem Statement

Zeph makes Users wait too long, and it misses what they point at.

1. **The wait is slow and the same for everyone.** After each text, Zeph waits 15 seconds for the next one, and every new text restarts the 15 seconds. A User who sends one clear question ("what do you think I should do?") still waits 15 seconds plus the time to write the reply. A User who sends five quick texts waits over a minute. Real people talk both ways: sometimes one long text, sometimes a burst of short ones across several threads. A friend answers when you seem done, not after a fixed clock.

2. **Zeph can't see a reply to a specific text.** In Telegram, a User can swipe on an earlier text to reply to it. Zeph ignores that link (except for stickers) and reads the reply as a new, unconnected thing. "not yet, scared tbh", sent as a reply to "have you told your mum about the job yet?", reaches Zeph as just "not yet, scared tbh". The same goes for a User pointing at their own old text to say "like I said before". It is also a safety gap: a "yes" sent as a reply to Zeph asking about self-harm reaches the Safeguard as a bare "yes".

3. **Zeph's own replies to a multi-thread burst are hard to follow.** When a User sends "work was rough" / "also mum called" / "oh and the cat's sick", Zeph's several short texts don't show which one answers which.

## Solution

1. **The wait follows how the last text reads.** If it reads as finished (a question, or a long full thought), Zeph waits briefly (2s by default). If it trails off ("and…", "so", "wait", a photo with no caption), Zeph waits longer (12s). Anything else gets a middle wait (6s). However many texts come, no Message waits more than a cap (20s) from its first text. If Zeph guesses wrong and the User keeps typing before any reply has gone out, Zeph already drops what it was writing and answers everything together (start-over, built 23 Nov 2026), so a short wait can't cut the User off. Admins set every number and word list on the Platform settings page, each with a hint saying what it does and how it changes Zeph's replies.

2. **Zeph reads Replied-to Texts.** When a User replies to an earlier text, Zeph's or their own, however old, Zeph sees who sent it, when, and what it said (or only the part the User highlighted). The Safeguard, Understanding, Recall, Reply Plan and Reply all see it. Recall also searches by it, so a reply to an old text brings back the old story.

3. **Zeph replies to a specific text when it helps.** When a Message has more than one thread and one of Zeph's texts answers a User text that isn't the latest, Zeph sends it as a reply to that text, at most once or twice per reply.

## User Stories

### The wait

1. As a User, I want a clear question to get a reply within a few seconds, so that talking to Zeph feels like talking to a friend who is paying attention.
2. As a User, I want one long text with a finished thought answered quickly, so that I'm not left waiting after saying everything I meant.
3. As a User, I want Zeph to wait longer when my text trails off ("and…", "so", "but"), so that I'm not cut off mid-thought.
4. As a User, I want Zeph to wait longer when I send a short opener like "wait", "ok so", "hmm" or "lol", so that it hears the thought that follows.
5. As a User, I want Zeph to wait for my explanation after I send a photo with no caption, so that it answers the photo and what I say about it together.
6. As a User, I want a sticker sent on its own to get a normal wait, so that it is neither rushed nor left hanging.
7. As a User who sends a burst of short texts, I want Zeph to answer them all together in one reply, so that it answers my whole thought, not half of it.
8. As a User who keeps typing for a long time, I want Zeph to reply within a set time of my first text, so that the chat never feels dead.
9. As a User, if I send another text while Zeph is still writing and nothing has gone out yet, I want Zeph to start over with everything I said, so that a short wait never costs me a half-answer.
10. As a User, I want typing to show from my first text until Zeph's reply arrives, as it does today, so that I know Zeph is there.
11. As a User sending an Album, I want Zeph to wait for every photo before the new rules apply, so that the Album is still answered as one.
12. As a User in crisis, I want the Safeguard to check each text as it arrives, unaffected by the wait, so that help is never held back.
13. As a User, I want a Message to count once toward my Daily Message Limit however the wait plays out, so that the new timing never uses up my limit.
14. As an Admin, I want to set the wait for a text that reads finished, so that I can tune how fast Zeph answers clear questions.
15. As an Admin, I want to set the wait for a text that trails off, so that I can tune how much room Zeph gives an unfinished thought.
16. As an Admin, I want to set the wait for any other text, so that I can tune the everyday pace.
17. As an Admin, I want to set the cap from a Message's first text, so that no User waits too long however many texts they send.
18. As an Admin, I want to set how many words make a text "long", so that I can decide when a full sentence counts as finished.
19. As an Admin, I want to edit the list of trailing words and short openers, so that I can add the slang and fillers our Users actually use.
20. As an Admin, I want every one of these settings to show a short hint saying what it is and how it changes Zeph's replies, so that I can change them safely without reading code.
21. As an Admin, I want a change to these settings to apply from the next text, so that I can try a new value and see its effect quickly.
22. As an Admin, I want the settings to start from sensible defaults (2s, 12s, 6s, cap 20s, 15 words), so that Zeph feels natural without any tuning.
23. As an Admin who has already changed the old single wait, I want my value kept as the "other" wait, so that my choice isn't silently thrown away.

### Replied-to Texts

24. As a User, when I reply to one of Zeph's texts, I want Zeph to know which text I'm answering, so that "not yet, scared tbh" is read as an answer to its question.
25. As a User, when I reply to one of my own old texts, I want Zeph to know what I'm pointing at, so that "like I said before" makes sense to it.
26. As a User, when I highlight part of a text and reply to it, I want Zeph to see just that part, so that it knows exactly which bit I mean.
27. As a User, when I reply to a text from weeks ago, I want Zeph to bring back what we were talking about then, so that we can pick up an old story.
28. As a User, when I reply to a text older than Message Retention, I want Zeph to still see what it said, so that old replies keep working after the messages are deleted.
29. As a User, when I reply to a photo or a sticker, I want Zeph to know that's what I'm replying to, with any caption, so that my reply makes sense.
30. As a User, when I reply to a Check-in, I want Zeph to know I'm answering that Check-in, so that its answer follows on from it.
31. As a User in crisis, when I answer "yes" as a reply to Zeph asking whether I'm thinking of hurting myself, I want the Safeguard to read my "yes" with that question, so that I get the Crisis Reply.
32. As a User, when several of my texts in one Message reply to different texts, I want Zeph to see each link, so that it doesn't mix up my answers.
33. As a User, I want replies to stickers to keep working as they do today, so that nothing I rely on breaks.
34. As an Admin, I want a User's text and what it replies to shown clearly in the Model Call Log where content is shown, so that I can see why Zeph answered as it did.

### Zeph replying to a specific text

35. As a User who sends several threads in one Message, I want Zeph's answer to an earlier thread sent as a reply to that text, so that I can see which thread each part answers.
36. As a User, I want Zeph to do this only when it helps, at most once or twice per reply, so that it doesn't feel robotic.
37. As a User who sends one thread, I want Zeph's reply sent normally, so that a simple chat stays simple.
38. As a User, I want Zeph never to reply to a text that isn't part of my Message, so that its replies never point at the wrong thing.
39. As a User, if Telegram refuses to attach Zeph's text to mine, I want the text sent anyway, so that I still get the reply.

## Implementation Decisions

### The wait

- **Wait rule (new, plain code, pure).** One small module decides the wait for the latest text: given the text (its words, kind, whether it has a caption) and the Platform Settings, it returns which kind the text is (**finished**, **trails off**, **neither**) and the seconds to wait. It is a pure function so it is easy to test and reason about.
  - **Finished:** the text ends with `?`, or has at least the "long" word count and ends with `.`, `!` or an emoji.
  - **Trails off:** the text ends with `...` or `…` or `,`; or its last word is in the trailing words list; or the whole text is one of the short openers in that list (e.g. `wait`, `ok so`, `lol`, `hmm`). A photo with no caption trails off.
  - **Neither:** everything else, including a sticker on its own and a photo with a caption that is neither.
  - Matching is case-insensitive and ignores trailing spaces.
- **Cap.** The handler remembers when the Message's first text arrived. Each wait is the rule's seconds or the time left to the cap, whichever is shorter (never below zero). The cap counts from the first text of the Message, including texts added by start-over.
- **Where it plugs in.** The incoming message handler's wait restart calls the wait rule instead of reading the single wait setting. Albums keep their current behaviour: the wait for an Album item still restarts as each photo arrives, and the rule applies to the Album as one text (a captionless Album trails off).
- **Start-over is unchanged** (ADR-0018 per-User queue lines). A text before any reply has gone out drops the reply; after, it starts the next Message.
- **Platform Settings.**
  - `message_wait_seconds` stays as the **neither** wait (its hint is rewritten).
  - New: `message_wait_finished_seconds` (2), `message_wait_trailing_seconds` (12), `message_wait_cap_seconds` (20), `message_wait_long_text_words` (15), `message_wait_trailing_words` (a list of words and short openers).
  - Each is an editable setting with a required hint (existing rule: one or two sentences, what it is, how it changes Zeph's replies). They sit together in the same section of the Platform settings page as the current wait.
  - Validation: whole seconds 0 to 60; the cap at least as large as the longest of the three waits; word count 1 to 100; the words list non-empty, each item trimmed and lower-cased.
- **Migration.** Adds the new settings with their defaults. Moves `message_wait_seconds` from 15 to 6 only where it is still the seeded 15 (as migration 0066 did); an Admin's own value is kept. No User data is touched.

### Replied-to Texts

- **Channel-neutral shape.** `IncomingMessage` gains a `replied_to` field: who sent the original (**User** or **Companion**), when it was sent, its kind (text, photo, sticker, other) and what it said: the highlighted part if the User highlighted one, otherwise its text or caption, cut to about 500 characters. The existing `replied_sticker` stays and is filled as today.
- **Telegram adapter.** Parsing reads `reply_to_message` (sender's `is_bot` decides User or Companion, `date`, `text`/`caption`, photo or sticker) and the update's `quote` (the highlighted part) for text, sticker and photo messages. It never needs to look up our saved messages, so it keeps working after Message Retention.
- **Saved with the text.** Each saved User text keeps its Replied-to Text (a new nullable JSON column on the conversation messages). This is how later replies in the Conversation and the Recent Messages see it. Delete My Data and Message Retention remove it with the text.
- **Shown in every transcript.** The one place that turns saved messages into transcript lines writes a text with a Replied-to Text as, for example: `User (replying to Zeph's text from 3 Nov, "have you told your mum about the job yet?"): not yet, scared tbh`. A reply to the User's own text says "their own text". This one change reaches the Safeguard, the Understanding, the Reply Plan and the Reply, because each builds its transcript from the same lines.
- **Safeguard.** Reads each text with its Replied-to Text as it arrives. Same call, a little more input.
- **Recall.** The search text for Life Threads, Patterns (and Move Outcomes' text search) adds the Replied-to Texts of the Message's texts to what the Understanding says the User means and the latest texts.
- **Model Call Log.** Shows the Replied-to Text with the text wherever it already shows content (ADR-0010 rules unchanged).

### Zeph replying to a specific text

- **Saving the chat's ID.** Each saved User text keeps its chat channel message ID (a new nullable column), so Zeph can point at it.
- **Reply input and output.** The Reply is shown the Message's texts numbered (`[1]`, `[2]`, …). Its prompt says when to point (more than one thread, the text answers one that isn't the latest, at most two per reply) and how: a part may start with `[re 2]`. Code strips the marker. A marker that names no text of this Message, or one past the per-reply limit, is dropped and the part is sent normally. `response_prompt` is reloaded from the seed by migration.
- **Chat channel port.** `send_text` gains an optional "reply to this message ID". The Telegram adapter sends it as `reply_parameters` with `allow_sending_without_reply` on, so a deleted or refused original never stops the text going out.
- **Composed reply.** Each part carries the optional ID it replies to; the rest of sending (typing pause, stickers, Shared Photo, start-over before the first part goes out) is unchanged.

### Docs

- `CONTEXT.md` already has the new **Message** wording and the **Replied-to Text** entry. `docs/message-pipeline/README.md` decisions 19–21 and the step 2 note change from "agreed, not built" to "Built" notes as each part lands.
- No ADR: all of this is settings and behaviour that are easy to change later.

## Testing Decisions

- **Good tests check what a User or Admin would see**, through the webhook and the fakes, not the inner calls. They name the behaviour in plain words, like the existing ones (`test_a_text_sent_while_a_reply_is_written_starts_it_over_with_every_text`).
- **One seam, already in use:** post Telegram updates to the webhook in the test client, as `tests/test_messages.py` does, and check:
  - `FakeTimer.waits`: the wait each text got (finished, trails off, neither, photo with no caption, sticker, Album) and that the cap holds across a long burst and across start-over.
  - The fake chat model's prompts: the Safeguard, Understanding, Reply Plan and Reply each see the Replied-to Text in the transcript (Zeph's text, the User's own text, a highlighted part, a photo, a sticker, a Check-in); Recall's search includes it.
  - `FakeChatChannel`'s sent texts: a `[re N]` part goes out as a reply to the right User text; a bad or extra marker is dropped and the part sent normally; a single-thread Message sends nothing as a reply.
  - A crisis case: "yes" sent as a reply to Zeph's self-harm question reaches the Safeguard with that question.
- **Admin settings:** through the Admin settings API, like `tests/test_admin_settings.py`: the new settings are listed with non-empty hints, saved, validated (the cap below a wait is refused), and used from the next text.
- **Migrations:** like `tests/test_message_wait_migration.py`: the old wait moves 15 → 6 only when unchanged; new settings land with defaults; the new message columns are added without touching existing rows; `response_prompt` reloads.
- **Telegram adapter parsing:** update dicts built with `tests/telegram_helpers.py` (add a helper for a reply update with and without a `quote`).
- **Dashboard:** the Platform settings page shows the new fields with their hints (Vitest + React Testing Library, as the existing settings page tests do).
- **Running-app check (`/run`):** in a worktree, post updates to the backend webhook and watch the real timing and the reply links. No Evals are needed (they cost money).

## Out of Scope

- Learning each User's typing rhythm to set their wait. Left out until real chats show slow typists being cut off.
- A model call to judge whether a text is finished.
- Measuring time to reply or counting start-overs, on the Dashboard or in logs.
- Seeing when a User is typing (the Telegram Bot API doesn't offer it).
- Edited texts: an edit to a text already sent is not read again.
- Zeph replying to its own earlier texts, or to User texts from earlier Messages.
- Replies inside Albums beyond what the first item carries.

## Further Notes

- Platform is live with real Users (since 22 Nov 2026): migrations must keep all User data and an Admin's own setting values.
- Shorter waits mean more start-overs on long bursts, so a few more dropped model calls. That is accepted for faster replies.
- The design is agreed in `docs/message-pipeline/README.md` (decisions 19–21) and `CONTEXT.md` (**Message**, **Replied-to Text**).

## Completion

- Completed: 2026-11-23, all five issues verified and archived in `.scratch/natural-replies/issues/archive/`.
- Commits: 01 d710295, 02 a279e3f, 03 247ed18, 04 05d0766, 05 edbb74c, 06 552bfe9 (merges; each issue's Completion lists its work commits).
