# PRD: Get curious — the Companion gets to know the User

Status: completed

## Problem Statement

The Companion listens but doesn't get to know the User.

- In a real chat, a morning Check-in got the reply "It's going to be a long day. 5 hours sleep only. My mum spent the week with me in my house in Malaysia. She's back to Singapore this morning." Both Messages were read as Be heard, with no Moves. Zeph reflected back ("five hours and a long day ahead is a hard pairing") and then guessed a feeling ("the quiet probably lands even heavier") instead of asking. A friend would have asked "what's on today?", "how come only 5 hours?" or "you a coffee person?".
- Be heard's "when it fits" includes "sharing something painful or frustrating", with nothing about how strong the feeling has to be. So any mention of a hard thing, even in passing, reads as venting, and Be heard rules out asking why.
- Nothing makes Zeph curious in the moment. It asks only when it can't tell what the User wants (Ask more), when a strong mood has no known cause (asking why), or through Curiosities saved for later.
- Zeph has no way to hold something it suspects but isn't sure of. Every Memory Item looks equally true, and the User Portrait's "open questions" are shown to the User.
- A vent where Zeph only listened is never brought back later, unless the Understanding happened to hold a next Move.

## Solution

- A new Move, **Get curious**: one natural question about something the User just said, to learn something new about them, go a little deeper, or check something Zeph isn't sure of. It can be practical and kind ("you a coffee person?"), never a quiz. Most Needs allow it.
- Be heard is only for when the User is dwelling on something painful. A hard thing mentioned in passing (tired, a long day, a small annoyance) is Just chatting.
- Moves get an Admin checkbox, **Asks a question**. A Move marked this way is never made in two replies in a row, and never in the same reply as another question (asking why or a raised Curiosity). The other question wins.
- Curiosities can hold a **guess**: something Zeph suspects about the User, with how sure it is. Guesses are hidden from the User (ADR-0017), never stated as fact, and checked gently through Get curious, a woven-in question or the Curiosity Check-in. Once the User answers, the guess is closed and what they said is kept as a Memory Item.
- A vent where Zeph only listened becomes a look-back Curiosity, asked at least a day later.
- The User Portrait holds only what Zeph is fairly sure of. Its open questions move into Curiosities.

## User Stories

1. As a User, I want Zeph to ask about something I mentioned in passing, so that it feels like talking to a friend who's interested in me.
2. As a User who says "5 hours sleep only", I want Zeph to ask why or what's on today, so that it doesn't just guess how I feel.
3. As a User, I want Zeph to ask at most one question in a reply, so that the chat doesn't feel like an interview.
4. As a User, I want Zeph not to ask me something in every reply, so that I can just talk without being quizzed.
5. As a User, I want Zeph's questions to come from what I just said, so that they feel natural, not random.
6. As a User, I want Zeph to prefer asking about things it doesn't know yet about me, like my work, routines and the people in my life, so that it gets to know me over time.
7. As a User, I want Zeph sometimes to go deeper on something it half-knows, so that it understands me better than a surface fact.
8. As a User, I want Zeph to check something it isn't sure of ("your mum's in Singapore, right?"), so that it doesn't hold wrong beliefs about me.
9. As a User, I want Zeph never to state a guess about me as fact, so that it doesn't get me wrong out loud.
10. As a User, I want a small practical touch now and then ("you a coffee person?"), so that Zeph feels caring, while it still never pretends to be human.
11. As a User who gives a short answer to a question, I want Zeph to let it go, so that I don't feel pushed.
12. As a User who is really venting, I want Zeph to listen and not ask why I feel this way, so that I feel heard.
13. As a User who is venting, I want Zeph still free to ask about what happened ("what did he say?"), so that it understands the situation.
14. As a User who mentions a hard thing in passing, I want Zeph to keep it light, not treat it as a crisis or a vent, so that the conversation matches my mood.
15. As a User who vented and was only listened to, I want Zeph to gently ask how I see it now, a day or more later, so that I can reflect once it's settled.
16. As a User, I want that look-back never to come in the same few hours, so that it doesn't reopen something raw.
17. As a User who brushes off a look-back or a question, I want Zeph to stop pushing, so that I keep control of what we talk about.
18. As a User, I want my answers to Zeph's questions remembered as usual, so that it doesn't ask the same thing again.
19. As a User, I want my answer to a guess to correct what Zeph believes, so that its picture of me is right.
20. As a User, I want my User Portrait to show only what Zeph is fairly sure of, so that I'm not shown half-formed guesses as if they were known.
21. As a User, I want Delete My Data and Account Deletion to remove Zeph's guesses about me, so that nothing about me is kept after I ask.
22. As a User who deletes a Memory Item or Life Thread, I want guesses that came from it removed too, so that it is never used again.
23. As a User with User Memory off, I want no new guesses made, so that "stop learning" means what it says.
24. As a User with Curiosities off for me, I want no guesses made or raised, so that the Feature switch is respected.
25. As a User, I want a guess raised through a Curiosity Check-in to read like a friend wondering, not a form to fill in, so that Check-ins still feel personal.
26. As a User, I want Zeph not to ask a Get curious question while it's already asking why I feel something, or bringing up a Curiosity, so that I get one question at a time.
27. As a User who is struggling, I want any question to be about what happened, never why I feel it, so that I feel supported, not analysed.
28. As a User, I want Zeph to learn whether I like being asked things, so that it asks more if I enjoy it and less if I don't.
29. As an Admin, I want Get curious seeded as a Move I can edit like any other, so that I can tune how Zeph asks.
30. As an Admin, I want an "Asks a question" checkbox on every Move, so that I can apply the one-question rules to any Move I add.
31. As an Admin, I want Get curious seeded with "Asks a question" ticked, so that it works well from the start.
32. As an Admin, I want Get curious ruled out by Ask more and Get it done, and allowed by the other Needs, so that it isn't used where it doesn't fit.
33. As an Admin, I want the new Be heard and Just chatting wording applied to my running platform, unless I've edited them, so that my own edits are never lost.
34. As an Admin, I want the Curiosity-keeping and Portrait prompts updated on my running platform, so that guesses and look-backs start working without manual steps.
35. As an Admin, I want a new install to get all of this from the seed files, so that new and old platforms match.
36. As an Admin, I want Understanding Eval Cases for the passing update, the real vent and the guess check, so that I can measure this with the real model when I choose to.
37. As an Admin, I want Eval Runs to keep each Move's "Asks a question" setting in their snapshot, so that later changes don't alter past results.
38. As an Admin, I want a Move that was dropped because another question won not recorded as made, so that Move Outcomes learn only from what the User actually got.
39. As an Admin, I want the Model Call Log to keep showing the lead, supporting and next Moves for every User without content, so that I can see when Get curious is used.
40. As the owner, I want a separate issue for a Curiosity-keeping Eval, so that I remember to build it later.

## Implementation Decisions

- **Get curious is Admin-managed data** (ADR-0004, ADR-0016), added to the Moves seed. Its "when it fits" covers the User mentioning something about their life (plans, people, sleep, routines, work) that Zeph knows little about, half-knows, or isn't sure it has right. Its "how to do it" says to ask one short, light question about something they just said, the way a curious friend would; to prefer what Zeph doesn't know yet, or a guess it holds; that checking something it thinks it knows is fine when it isn't sure; that it can be practical and kind; that it's never a quiz; and to let it go after a short answer. It needs no Feature.
- **Needs.** Ask more and Get it done rule out Get curious; the other Needs allow it. Be heard's "how to reply" already allows "a short question that invites more" and bans "why they feel this way" while venting, which matches.
- **Be heard / Just chatting wording.** Be heard's "when it fits" becomes roughly: "They're letting out something painful or frustrating, staying on it or coming back to it, often with strong words, and want it to land with someone, not to be fixed… A hard thing mentioned in passing (tired, busy day, a small annoyance) is not this: that's an update." Just chatting's "when it fits" adds "including passing mentions of everyday hard things, like poor sleep or a long day."
- **"Asks a question" on Moves.** It's a new boolean on a Move's details: shown, edited and saved on the Dashboard Moves page and the admin Moves API, default off, and ticked for Get curious in the seed. Code never looks up a Move by name. The core rules:
  - A Move marked this way that the previous Understanding in the Conversation made, as lead or supporting, is left out of the Moves offered to the Understanding. This is a generic filter, alongside the one for a Move's needed Feature.
  - When the Understanding makes such a Move while the reply also asks why or raises a Curiosity, the Move is dropped from that reply: it isn't put in the reply's instructions and isn't recorded as made, so no Move Outcome is kept for it. If it was the lead Move, the supporting Move, if any, doesn't move up; the reply just responds.
  - A Woven-in Check-in is decided after the Understanding. When the reply already asks a question (through a Move marked this way, asking why or a Curiosity), the Check-in model is told so and prefers to leave the Check-in out or weave it in without another question.
  - Like a Move's needed Feature, a Variant's Setting Overrides can't change it; the Eval Run snapshot of Moves keeps it.
- **Curiosity guesses (ADR-0017).** Curiosities get two optional fields: the guess (what Zeph suspects, e.g. "their mum lives in Singapore") and how sure it is (low, medium or high). Both are empty for a plain Curiosity. The Curiosity-keeping step:
  - may write a guess for something the User hinted at without settling, or something Zeph may have got wrong;
  - closes a waiting guess once the User has answered it, and the Memory Item keeping step saves what they said, so the answer is never written as a new guess.
- **How a guess is shown.** The Understanding sees a due guess Curiosity with its guess and how sure Zeph is, marked as not known and to be checked gently. When one is raised, in a reply or the Curiosity Check-in, the reply or Check-in is told that it's a guess to check, never a fact to state.
- **Limits.** Guesses share the existing Curiosity waiting limit and per-Conversation raise limit. A Get curious question made in the moment, not from a saved Curiosity, doesn't count toward the raise limit.
- **Look-back Curiosities.** The Curiosity-keeping prompt adds: something they vented about where Zeph only listened becomes a gentle look-back, asking how they see it now, with not_before at least the next day and sensitivity at least medium.
- **Portrait.** The Portrait prompt drops "Open questions Zeph is still curious about" and says to write only what Zeph is fairly sure of.
- **Reaching the running platform.** One migration:
  - adds the "asks a question" column (default false) and the two Curiosity columns;
  - adds Get curious if no Move with that name exists, with "asks a question" ticked, placed last in the order, and ruled out by Ask more and Get it done if they still exist;
  - updates the wording of Be heard and Just chatting only where it still matches the old seed word for word;
  - reloads the Curiosity-keeping and Portrait prompts from the seed by deleting their stored values, as earlier prompt migrations do.
  The seed files get the same changes.
- **Glossary and ADR.** These are already updated: CONTEXT.md (Move, Curiosity, User Portrait) and ADR-0017.

## Testing Decisions

- Tests check behaviour from the outside: what the Understanding was offered, what the reply was told, what's saved and what the Dashboard shows. They don't check private helpers or prompt-building internals beyond the text the model receives.
- **Telegram webhook with the scripted chat model** (the main seam; prior art: test_next_move, test_moves, test_understanding). It covers:
  - Get curious offered under the Needs that allow it and not under Ask more or Get it done;
  - a Move marked "asks a question" made in the last reply not offered next time, and offered again the reply after;
  - such a Move dropped and not recorded as made when the reply also asks why or raises a Curiosity;
  - a due guess Curiosity shown to the Understanding as a guess with how sure Zeph is, and the reply told to check, never state it;
  - the Woven-in Check-in model told when the reply already asks a question.
- **Conversation end** (prior art: test_curiosities, test_post_conversation). It covers:
  - a guess saved with how sure Zeph is;
  - an answered guess closed;
  - no guesses made while User Memory or Curiosities don't work;
  - the Portrait prompt no longer asking for open questions;
  - Delete My Data and deleting the source Memory Item removing guesses.
- **Curiosity Check-in** (prior art: test_curiosity_check_in): a guess raised by a Check-in is sent as a gentle check.
- **Migration** (prior art: test_moves_migration). It covers:
  - Get curious added with the right rule-outs and the checkbox ticked;
  - unchanged Need wording updated and edited wording left alone;
  - prompts reloaded;
  - a database that already has a "Get curious" Move left as it is.
- **Admin Moves API** (prior art: test_admin_moves): "asks a question" saved and returned.
- **Dashboard** (prior art: MovesManager.test.tsx, Vitest + React Testing Library): the checkbox shows on each Move and saves.
- **Eval Cases** (seed data, prior art: the Understanding Eval seed cases). Three new Understanding cases:
  - the passing update ("long day, 5 hours sleep only" after a morning Check-in) → Just chatting with Get curious;
  - a real vent → Be heard, no question about why;
  - a waiting guess about mum, and the User mentions her → Get curious checks it gently.
  These are not run as part of this work, since Evals cost money; the owner decides when.
- Curiosity keeping (look-backs and guesses) is also checked by `/run` on a real Conversation end, since there's no Curiosity-keeping Eval yet.
- Checks: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, and in `web/` `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`.

## Out of Scope

- A **Reflect** Move for looking back on a vent together. It'll be grilled in its own session; here the look-back is only a Curiosity.
- A **Curiosity-keeping Eval**, tracked in `.scratch/curiosity-keeping-eval/issues/01-curiosity-keeping-eval.md`, to be grilled first.
- A certainty marker on Memory Items.
- Showing Curiosities or guesses to Users or Admins on the Dashboard.
- An Admin-set cap on how many Get curious questions a Conversation may have.
- Changing the ask-why rule, which stays fixed in code.
- Running Eval Runs.

## Further Notes

- Grilled 2026-11-18. Decisions are recorded in CONTEXT.md and ADR-0017; Get curious follows ADR-0016.
- The platform isn't live yet, so reloading prompts from the seed (and losing any hand edits to those two prompts) is acceptable.
- Move Outcomes already learn per User whether a Move helped, so whether a User enjoys being asked things is learned without new work.

## Completion

- Completed: 2026-11-18
- Delivered by issues 01–04 (all archived in `.scratch/get-curious/issues/archive/`):
  - 01 "Asks a question" checkbox on Moves: d553b87, review fixes 8ff7363, run fix f79905b, renumber e1ffaf5, archive aea45e3, merge 55c9dbf
  - 02 Curiosity guesses: e7e484f, review fixes 45a72a1, run fix 30b8327, archive be3d78f, merge 465ce4e
  - 03 Get curious Move and the venting line: 70c2e75 (includes review fixes), CONTEXT.md 2a8647c, archive 17eeb13, merge 15be1d5
  - 04 Look-backs, Portrait and the guess Eval case: 2dd66b5, review fixes 0de4dba, archive 1f3e5bd, merge 6d87f34
- The Curiosity-keeping Eval (story 40) is its own issue: `.scratch/curiosity-keeping-eval/issues/01-curiosity-keeping-eval.md` (needs-triage).
- The three new Understanding Eval cases (passing update, real vent, guess check) are in the seed and have not been run; the owner decides when.
- Checks on close-out (main at 15be1d5, same tree as the tested issue 03 branch): ruff, ruff format, mypy pass; pytest 1319 passed; pnpm lint, format:check, typecheck pass; Vitest 486 passed
