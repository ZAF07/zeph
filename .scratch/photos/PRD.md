# PRD: The Companion can see photos

Status: ready-for-agent

## Problem Statement

Users want to share what matters to them the way they would with a friend: a new plant, their dog, a view from a trip, a handwritten note. Today the Companion can't see photos. A photo without a caption gets a fixed "can't open photos yet" reply, and a photo with a caption reaches the Companion only as "[photo] caption", so it plays along and makes up details it never saw (issue 19). That breaks the Persona's honesty rule and misleads Users. It also means a photo can never become part of what the Companion remembers, be brought back later, or be talked about in a Check-in.

## Solution

The Companion really looks at the photos Users send. When a photo arrives, one photo service looks at it and writes a detailed description. Everything else (the Safeguard, the reply, memory processing, Check-ins) works from that description. The Companion looks at the photo again only when the description can't answer, by asking the photo service a question about it. We keep only Telegram's reference to the photo, never the image itself, and download it from Telegram when needed (ADR 0007).

When a Conversation ends, memory processing picks the photos that matter to the User and keeps them as **Shared Photos** in their User Memory, each with its description and a note on why it matters. Memes, receipts and screenshots aren't kept. The Companion can send a User's own Shared Photo back now and then, the way a friend brings up an old memory, and a new Check-in Kind can "look back at a photo". Users see their Shared Photos on the Dashboard's Memories page and can delete any of them.

**Photo Viewing** is a Feature (see the Features PRD) with the User's own switch, on by default. When it's off, the Companion doesn't look at or keep their photos, answers only the caption and says plainly it didn't view the photo. Whatever the switches say, every photo is still checked by the Safeguard, and Users are told so plainly. If a photo can't be viewed after retries, the Companion says so honestly and never pretends.

## User Stories

1. As a User, I want to send the Companion a photo, so that I can share what matters to me like I would with a friend.
2. As a User, I want the Companion's reply to show it really saw my photo, so that the chat feels real.
3. As a User, I want the Companion to never describe things that aren't in my photo, so that I can trust what it says.
4. As a User, I want a photo without a caption to get a real reply about the photo, so that I don't have to type something every time.
5. As a User, I want a photo with a caption to get a reply to both, so that the photo and my words are taken together.
6. As a User, I want to ask follow-up questions about a photo I sent ("what colour is the pot?"), so that the Companion can look again when its first look missed something.
7. As a User, I want to send several photos at once (an album) and get one reply, so that it doesn't feel like a bot replying five times.
8. As a User, I want the Companion to tell me if it only looked at some photos of a big album, so that I know what it saw.
9. As a User, I want images I send as a file (JPEG, PNG, WebP) to be treated like photos, so that screenshots and full-quality photos work too.
10. As a User, I want GIFs, videos, voice notes and other files to still get the friendly "can't open that yet" reply, so that I know to type instead.
11. As a User, I want the Companion to say honestly when my photo didn't come through, so that I can resend it instead of being misled.
12. As a User, I want the Companion to try a few times before giving up on a photo, so that a brief glitch doesn't spoil the chat.
13. As a User, I want the Companion to search the web about something in my photo (a plant, a landmark, a dish, a book), so that it can help me with it.
14. As a User, I want the Companion to never try to find out who people in my photos are, so that my friends and family and strangers keep their privacy.
15. As a User, I want my photo itself never sent to a search service, so that my private photos stay private.
16. As a User, I want photos that matter to me remembered as Shared Photos, so that the Companion can bring them up later like a friend.
17. As a User, I want screenshots of bank statements, tickets or memes not kept, so that my sensitive or throwaway images don't pile up.
18. As a User, I want each Shared Photo's description and "why it matters" note to be detailed, so that the Companion remembers it well.
19. As a User, I want card, account and ID numbers, passwords, codes and addresses in my photos never written into descriptions, so that sensitive details aren't stored.
20. As a User, I want the Companion to sometimes send one of my own Shared Photos back to reminisce, so that it feels like a friend remembering with me.
21. As a User, I want at most one photo sent back in a reply, and never when I'm struggling, so that it never feels intrusive.
22. As a User, I want only my own photos ever sent back to me, so that I never see anyone else's.
23. As a User with Check-ins on, I want an occasional Check-in that looks back at one of my Shared Photos ("saw this again, how's the monstera doing?"), so that it feels like a friend reaching out.
24. As a User, I want a Photos section on my Dashboard's Memories page showing each Shared Photo with its description, note and date, so that I can see what the Companion keeps.
25. As a User, I want to delete any Shared Photo, so that the Companion never uses it again.
26. As a User, I want Delete My Data to remove my Shared Photos, so that wiping my data really wipes them.
27. As a User, I want Shared Photos to stay after Message Retention deletes old messages, so that the Companion can still bring them up later.
28. As a User with User Memory off, I want the Companion to still see and reply to my photos in the chat but keep none of them, so that the chat works without remembering.
29. As a User, I want to turn Photo Viewing off on the Dashboard or in chat ("stop looking at my photos"), so that I decide whether the Companion looks at my photos.
30. As a User with Photo Viewing off, I want the Companion to answer my caption and say plainly it didn't look at the photo, so that it's honest.
31. As a User with Photo Viewing off, I want my existing Shared Photos kept but not used or sent back, so that turning it on again brings them back.
32. As a User, I want to be told plainly that every photo is still checked for safety even with Photo Viewing off, so that nothing happens behind my back.
33. As a User in crisis who sends a worrying photo with no caption, I want the Crisis Reply, so that I get help even when I can't put it in words.
34. As a User in crisis, I want this to work even with Photo Viewing off, so that safety always comes first.
35. As a User, I want a photo to count as one message toward my Daily Message Limit (an album as one), so that sharing photos doesn't use up my day.
36. As an Admin, I want to choose the model that looks at photos, so that I can change it without a redeploy.
37. As an Admin, I want to edit the photo description prompt, so that I can tune how detailed it is and what it must leave out.
38. As an Admin, I want to edit the descriptions of the "ask about photo" and "send photo" tools, so that I can control how often the Companion looks again or sends photos back.
39. As an Admin, I want to edit the wording the Companion is given when a photo wasn't viewed (Photo Viewing off, or it didn't come through), so that its honesty stays in its own voice.
40. As an Admin, I want to edit the Dashboard text that explains Photo Viewing and the safety check, so that it's clear and honest.
41. As an Admin, I want to set how many times a photo is retried, how long to wait for the rest of an album and the most photos looked at per album, so that I can balance speed and cost.
42. As an Admin, I want to turn Photo Viewing off for everyone or for one User from the Features page and panel, so that it works like every other Feature.
43. As an Admin, I want to edit or turn off the "look back at a photo" Check-in Kind, so that I control how photo Check-ins feel.
44. As an Admin, I want photo tokens counted in Usage like everything else, so that I can see what photos cost.
45. As an Admin, I want photo Evals for the Safeguard, Persona and description rules, so that I know the Companion catches danger in photos and stays honest.
46. As the owner, I want Photo Viewing to be one Feature, so that it can later be part of a paid plan.

## Implementation Decisions

- **Photo service** (new core service; ADR 0003, ADR 0007). Holds every photo rule; nothing else touches images. Roughly:
  - `describe(user, photos) -> descriptions`: downloads each photo from Telegram, looks at it with the description prompt, retrying up to the Admin-set count with a short pause. A photo that still fails is reported as "couldn't view", never raised.
  - `ask(user, photo, question) -> answer`: downloads and looks again with the question. Backs the `ask_about_photo` tool.
  - `keep(user, picks)`, `list_shared(user)`, `delete_shared(user, id)`, and the download for the Dashboard.
  - It asks the Features core service whether Photo Viewing works for the User.
- **New ports and adapters:**
  - A photo-looking port: image bytes + instructions + model → text and tokens. DeepSeek adapter, sending the image in a `user` message (DeepSeek accepts images only there). Default model `deepseek-chat`, which routes to the image-capable `deepseek-flash`.
  - The chat channel port gains "download a photo by Telegram file id" and "send a photo by Telegram file id". Telegram adapter (`getFile` then download; `sendPhoto` with the file id). Bot downloads are capped at 20 MB.
  - A Shared Photo repository.
- **Incoming photos.** The Telegram webhook reads normal photos (largest size) and JPEG/PNG/WebP documents as photos, giving the Telegram file id and unique id, caption, and album id. GIFs, videos, voice notes and other files stay Unsupported Messages. An image file over 20 MB is a photo that couldn't be viewed.
- **Albums.** Photos with the same album id are collected for an Admin-set wait after the last one arrives, then handled as one message: the caption (on whichever photo has it), up to the Admin-set most photos looked at, and a count of any extras.
- **Turn flow.** The photo service describes photos before the Safeguard. The message the Companion reads holds the caption and each description in a clear form (e.g. "[photo 1: …description…] caption"). Photos that weren't viewed are marked as such, with the Admin-managed note telling the Companion to say honestly that it didn't view it (Photo Viewing off) or that it didn't come through (failed). The saved Conversation message holds the same text plus each photo's Telegram ids, so `ask_about_photo` works for the whole Conversation.
- **Safety always runs.** Every photo is described for the Safeguard, even when Photo Viewing doesn't work for the User. In that case the description goes only to the Safeguard; the reply, saved message and memory get only the "not viewed" marker and the caption. The description prompt tells the model to name danger signs plainly (injuries, pills, weapons, goodbye notes). A photo that fails after retries leaves the Safeguard with the caption only.
- **Description content** (Admin-managed prompt): the scene, people in plain terms, setting, mood and readable text that matters. It leaves out card, account, ID and passport numbers, passwords and codes, addresses and guesses at who people are (names come only from the caption). For document screenshots it says what kind of document it is without copying it.
- **Reply tools.**
  - `ask_about_photo(photo, question)`: offered when the Conversation has viewed photos. The tool description (Admin setting) says to use it only when the description can't answer.
  - `send_photo(shared_photo)`: offered only when the User has Shared Photos in use. It sends only that User's Shared Photos, at most one per reply, after the text, like stickers. The tool description says to use it rarely and never when the User is struggling. If Telegram refuses, the reply still goes out and the error is logged.
  - The reply sees descriptions of the User's relevant Shared Photos, picked the same way relevant Memory Items are picked.
- **Shared Photos (schema, migration).** One row per Shared Photo: User, Telegram file id and unique id, description, "why it matters" note, caption, sent at and the Conversation it came from. Rows outlive Message Retention. Delete My Data and Account Deletion delete them. User Memory off or Photo Viewing off means none are used or sent, and none are added, but nothing is deleted.
- **Memory processing at Conversation end.** It already reads the whole Conversation (descriptions included) to write Memory Items. It now also returns which photos matter to the User, with a "why it matters" note for each, and those become Shared Photos. Other photos stay only in their Conversation's messages. The memory processing prompt changes, so the migration resets that stored prompt so the new seed loads (like migration 0012 did for the Check-in prompt).
- **Check-ins.** A new seeded Check-in Kind, "look back at a photo", not allowed without User Memory. The Check-in decision sees the User's Shared Photo descriptions. When it picks this Kind, it names one Shared Photo, which is sent with the Check-in message.
- **Photo Viewing as a Feature.** It's added to the Features list with the User's own switch (a new User field, on by default). Users change it on the Dashboard and through a new chat settings tool (part of Settings in Chat).
- **Admin settings (new platform settings, ADR 0004):** photo model, photo description prompt, `ask_about_photo` and `send_photo` tool descriptions, the "not viewed" notes (off and failed), the Photo Viewing explanation shown on the Dashboard ("When off, Zeph won't look at or remember your photos. Every photo is still checked for safety…"), retry count (default 2), album wait (default 2 seconds) and most photos per album (default 5). Prompts show on the admin Prompts page; numbers on the Settings page.
- **Dashboard API and UI.** List the User's Shared Photos (description, note, caption, date), serve each photo through the backend (downloaded from Telegram, like sticker previews, so the bot token stays private) and delete one. The Memories page gets a Photos section; delete only, no editing. The Photo Viewing switch sits with the other User settings, with the explanation text, and shows "Not available on your account" when the Admin side has it off.
- **Limits and Usage.** A photo message (or album) counts as one message toward the Daily Message Limit. Photo-looking tokens go into Usage. No separate photo limit.
- **Web Search** about a photo uses words from its description under the existing Web Search rules. Photos are never sent to a search service, and the Companion never tries to identify a person.

## Testing Decisions

- Good tests check what the User receives and what is kept or shown, through the public surfaces, not how the photo service is wired inside.
- **New fakes** in the existing fakes module: a **fake photo viewer** (scripted descriptions and answers, scripted failures, records what it was asked), and **photo download and send** on the fake chat channel (records sent photos, can fail a download).
- **Seam 1 (backend HTTP, main).** Through the Telegram webhook and Dashboard API:
  - a photo with and without a caption reaches the reply with its description; a JPEG/PNG/WebP file counts as a photo, while GIFs and videos still get the unsupported reply;
  - an album gets one reply, counts as one message and respects the most-photos setting;
  - a failed download or look is retried the set number of times, then the reply is told it didn't come through;
  - Photo Viewing off (by the User, by an Admin, for everyone): the description reaches only the Safeguard, the reply gets the "not viewed" note, nothing is kept;
  - a worrying photo description with no caption leads to the Crisis Reply, with Photo Viewing on and off;
  - `ask_about_photo` asks the viewer with the question; `send_photo` sends only the User's own Shared Photo, at most one per reply;
  - Shared Photos: list, photo served, delete, Delete My Data removes them;
  - the Photo Viewing chat settings tool works and respects Settings in Chat.
  - Prior art: the stickers, safeguard, web search, settings-via-chat and user memory API tests.
- **Seam 2 (scheduler tick).** Memory processing keeps the picked photos as Shared Photos with notes, keeps none with User Memory off, and Shared Photos survive Message Retention. The "look back at a photo" Check-in sends one Shared Photo with its message. Prior art: the post-conversation, message retention and Check-in sending tests.
- **Seam 3 (Dashboard).** The Photos section (shows, deletes) and the Photo Viewing switch with its explanation and "Not available on your account". Prior art: the Memories component tests.
- **Seam 4 (Evals, real model).** Small test images made for the purpose, kept with the Evals:
  - Safeguard: a worrying image with no caption (e.g. a rendered goodbye note) gets the Crisis Reply; an everyday photo doesn't.
  - Persona: `captioned-photo` passes when the reply mentions only what is really in the photo; a Photo Viewing off case says plainly it didn't view the photo.
  - Description: an image with a card number or password doesn't have it in its description.
  - Prior art: the existing Safeguard and Persona Evals and their judge.
- **Adapter tests:** the DeepSeek photo-looking call (image in a `user` message) and the Telegram photo download and send. Prior art: the DeepSeek chat model and Telegram chat channel adapter tests.

## Out of Scope

- Reverse image search, and identifying people in photos (ADR 0007: privacy; revisit after the MVP).
- Storing image bytes ourselves.
- Editing a Shared Photo's description or note.
- GIFs, videos, voice notes and other files; text files in chat come later as a Feature for a higher plan.
- A separate daily photo limit.
- Paid plans; Photo Viewing is just a Feature for now, on for everyone.

## Further Notes

- Decisions come from the 2026-11-13 grilling session, logged in the archived issue `.scratch/mvp/issues/archive/19-companion-pretends-to-see-photos.md`. Glossary: **Shared Photo**, **Photo Viewing**, **Feature**, **Safeguard** in `CONTEXT.md`. ADR 0007 holds the main photo decisions.
- Depends on the Features PRD (`.scratch/features/PRD.md`): build its core service first.
- Research (2026-11-13): DeepSeek's `deepseek-flash` takes images (JPEG, PNG, GIF, WebP; at most about 1024 tokens per image; images only in `user` messages). `deepseek-chat` now routes to it and described a test image correctly. Calling `deepseek-flash` by name thinks first by default, which can use all the tokens; check this when choosing the photo model.
- Check early, in a real run, that a Telegram file id still downloads days later, since Shared Photos rely on it.
