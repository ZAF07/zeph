# Thought Experiments: an Admin guide

What a Thought Experiment is, how Zeph uses one, where to find material, how
to write a good one, how to manage them on the Dashboard, and what each
change does. For how the whole Pattern pipeline works, see
`docs/pattern-pipeline/README.md`. For the Pattern Types they tell apart, see
the Pattern Catalog (Admin → Pattern Catalog) and
`docs/pattern-catalog/README.md`.

## What it is

A **Thought Experiment** is a made-up situation, written to tell two
look-alike Pattern Types apart. Two Pattern Types can look the same from the
outside and differ in why. Someone who keeps quiet in a meeting may do it to
protect a relationship (CONF.AVOID.BELONG) or because a mistake would feel
like a verdict on them (ACH.WORTH.PERF). A good Thought Experiment puts the
User somewhere those two reasons pull in different directions, and asks what
they would do.

Example, for CONF.AVOID.BELONG and ACH.WORTH.PERF:

> Your team lead, who you get on well with, shares a plan in a meeting and you
> can see a real problem with it. Nobody else has spoken up. What do you do,
> and what's on your mind as you decide?

## How Zeph uses one

All of this is code. The model only words the question in the reply.

1. **When.** Only for a User with Pattern exploring on, and only for a
   suspected Pattern on their Agenda that has an **unclear** story: one the
   tagging step noted under two look-alike Pattern Types because it couldn't
   tell which.
2. **Its turn.** An Exploration tries the least pushy Approaches first: a follow-up
   on the story, then "would it have gone differently if…?",
   then a Thought Experiment, then "this week, notice when…". Zeph moves on
   to the next Approach only after a try came back vague or brushed off.
   Other needs (a counter-test, a missing Condition) skip the Thought
   Experiment.
3. **Which one.** Code takes the look-alike pair with the most unclear
   stories for that Pattern, and picks the oldest Thought Experiment for that
   pair that is on, not archived, and never put to this User before. If that
   pair has none left, it tries the next pair. If none is left at all, Zeph
   uses the next Approach instead.
4. **How often.** Never more than "Thought Experiments per Pattern a week"
   (Platform settings → Patterns, start 1) for one Pattern in 7 days. One
   waiting to be asked counts.
5. **Asking.** It becomes an aimed Curiosity that tells the reply to put the
   situation to the User in its own words. Zeph asks it in chat when the
   moment fits, or sends it as a Check-in of the "Something I've been
   wondering" kind, under that kind's weekly limit. Its sensitivity is the
   Curiosity's, so a sensitive one waits for a better moment.
6. **The answer.** At the end of that Conversation, the tagging step is shown
   the Thought Experiments asked in it. An answer to one is kept as an
   Observation of the **"what if"** kind, which counts for less than a real
   story (Platform settings → Patterns, "what if" 40%). So Thought Experiments
   point the Agenda and help settle look-alikes, but a Pattern can't become
   ready on made-up answers alone.

Zeph never says it is running a test, and never names a Pattern Type.

## Where they live

In the database, managed on the Dashboard (Admin → Thought Experiments).
Unlike Pattern Types, they need no deploy.

The first set comes from `src/companion/seed/thought_experiments.yaml`. Each
entry has a `key`. When the backend starts, it adds every seed entry whose key
isn't stored yet. An entry already stored is never touched, even if it was
edited, switched off or archived. So:

- A new entry in the seed file, with a new key, appears after the next deploy.
- Changing an entry in the seed file changes nothing that is already stored.
  Make the change on the Dashboard.
- Archiving one on the Dashboard is final: the seed never brings it back.
- Never reuse a key.

## The fields

| Field | What it is | What reads it |
|---|---|---|
| Wording | The situation and its question, as the User hears it. | The reply (in its own words) and the tagging step. |
| Pattern Type, Its look-alike | The two Pattern Types its answer tells apart, from the catalog. The order doesn't matter. | Code, to pick it for the pair with the most unclear stories. |
| Sensitivity | Low, medium or high, as a Curiosity's. | The Reply Plan and the Check-ins model, which are told it and wait for a better moment for a sensitive one. |
| Starter | Broad enough to put to a new User in their first Conversations. | Code, to pick the next one for a new User (see "Starters for new Users" below). Any Thought Experiment, starter or not, can also be picked for an Exploration. |
| On | Whether Zeph may ask it. | Code. Switching it off closes any Curiosity waiting to ask it. |

The Dashboard also shows how many times each one was asked.

## Where to find material

Start from the catalog itself. Each Pattern Type's look-alikes say how it
"tells apart" from the other one. That sentence is the heart of a Thought
Experiment: build a situation where the two reasons lead to different
choices. Every pair of look-alikes in the catalog should have at least one.

Other good sources, always rewritten in your own words:

- **Situational judgement tests** used in hiring: short workplace dilemmas
  with no right answer. Borrow the shape, not the items.
- **Vignettes from psychology research** on attachment, conflict styles and
  perfectionism, and the case examples in schema therapy books. They show
  which situations set each pattern off.
- **Everyday dilemmas** from advice columns and forums. Use the situation,
  never a real person's words or details.
- **What Users talk about.** The Agenda and the unclear stories show where
  Zeph is stuck. Write for those situations in general terms, never from one
  User's story.
- **Contrast pairs.** Write the same situation twice with one thing changed
  (a close friend or a shop, judged or not judged, certain or not). Which
  version is harder for the User tells you which reason drives them.

Never copy test items, questionnaires or published text word for word.

## How to write a good one

- **One situation, made up but ordinary.** Something most people have met or
  can picture: work, friends, family, a partner, money, plans.
- **Make the two reasons pull apart.** If both Pattern Types predict the same
  answer, it tells nothing. Check: "someone with the first would do X,
  someone with the second would do Y".
- **End with an open question.** "What do you do, and what's on your mind?"
  is better than "Would you speak up?". Asking what they'd think or feel, not
  only do, often tells more.
- **Leave every choice open and respectable.** No choice should sound weak,
  selfish or wrong.
- **Short.** Two to four sentences. It is read in a chat.
- **Second person, plain words.** "You", everyday language, no jargon.
- **No real crisis.** No grief, abuse, illness or danger. Keep it low stakes
  enough to answer over a cup of tea.
- **Sensitivity.** Low for work, friends and plans. Medium when it touches a
  partner, family or being hurt. High only when it must, and think twice.

Too leading:

> Your boss criticises your work in front of everyone. Surely you'd feel
> crushed, wouldn't you?

Better:

> Your manager tells you a report you wrote missed the point. What's the first
> thing you say or do? And what goes through your head about it that evening?

## The check for leading wording

When an Admin saves a Thought Experiment, code checks its wording (no model,
no cost) for:

- phrases that suggest the answer: "surely", "obviously", "of course",
  "wouldn't you", "don't you", "isn't it", "be honest", "most people would",
  "anyone would", "you probably", and a few more;
- words that make one choice sound bad: "selfish", "weak", "lazy", "needy",
  "clingy", "controlling", "overreact", "cowardly".

If it finds any, the save stops and the card lists each phrase with what to
change. The Admin can **Keep editing**, or **Save anyway** when the word is
fine where it is (for example "controlling" in a situation about someone
else). The check runs on every save, so it may ask again for one saved anyway.

It is only a check for words. It can't tell whether a question leaves both
choices open; read it with the rules above.

## Managing them

On the Dashboard, Admin → Thought Experiments:

- **Add**: "Add a Thought Experiment", fill in every field, Add.
- **Edit**: open its card, change it, Save.
- **Switch off**: turn "On" off and Save. It stays in the list, marked "Off",
  and can be switched on again.
- **Archive**: Archive in its card, then confirm. It moves to the archived
  list, read only. It can't be undone.

There is no delete. Tries that asked a Thought Experiment keep pointing at
it, so it is archived instead.

## What a change does

| Change | What happens |
|---|---|
| Add | Can be picked at the next Conversation end of any User whose unclear stories sit between its two Pattern Types. |
| Edit the wording | Used the next time it is picked. A Curiosity already waiting keeps the old words, and past tries keep the words they were asked with. |
| Change its Pattern Types | Picked for the new pair from the next Conversation end. A Curiosity already waiting is still asked. |
| Change the sensitivity | Used the next time it is picked. |
| Switch off | Any Curiosity waiting to ask it is closed at once, so it is never asked after. It isn't picked again until switched on. |
| Archive | As switching off, for good. It still shows in past tries and in its asked count. |
| Change "Thought Experiments per Pattern a week" | Applies from the next Conversation end. |
| Edit the seed file | Nothing for entries already stored; a new key is added on the next start. |

A User who was already asked one is never asked it again, even after an
edit.

## Starters for new Users

While Zeph is new to a User (their Familiarity, shown on the Users page) and
Pattern exploring works for them, code puts starter Thought Experiments to
them in their first Conversations:

- The oldest starter that is on, not archived and never put to them comes
  first.
- The next one is written when a Conversation ends, so the first is asked in
  their second Conversation.
- It is asked like any Curiosity: the Reply Plan picks the moment under the
  usual Need rules, and it may be skipped.
- Its answer is a "what if" answer. Such answers add to a Pattern's score but
  alone never make it suspected.

Three numbers on Platform settings (Patterns section) limit them:

| Setting | Starts at | What it does |
|---|---|---|
| Starter Thought Experiments for a new User | 4 | The most put to one User. |
| Days starter Thought Experiments are offered | 14 | Days after sign-up they are offered. |
| Starter Thought Experiments per Conversation | 1 | The most in one Conversation. |

They stop once Zeph is getting to know the User (by default 5 Conversations
and 3 Life Threads, or a first suspected Pattern), when the days have passed,
or when the User asks Zeph to drop one. To stop them for everyone, set the
first number to 0 or unmark every starter.

## The first set

31 Thought Experiments, drafted by Claude on 24 Nov 2026 for the owner to
review. They cover all 21 pairs of look-alike Pattern Types in the catalog,
two for the pairs most often confused, and five are starters, one per area:

| Area | Starter |
|---|---|
| Conflict | belong-worth-team-plan (CONF.AVOID.BELONG or ACH.WORTH.PERF) |
| Approval | give-belong-no-one-minds (APPR.GIVE.NEEDED or CONF.AVOID.BELONG) |
| Control | uncert-confirm-job-offers (CTRL.UNCERT.PLAN or APPR.CONFIRM.CHOICE) |
| Achievement | worth-uncert-two-presentations (ACH.WORTH.PERF or CTRL.UNCERT.PLAN) |
| Relationships | check-moodfix-quiet-evening (REL.CHECK.SECURE or REL.MOOD.FIX) |

None trips the leading-wording check. All 31 can be picked: every Pattern
Type they name is in the catalog.

## Limits

- The leading-wording check is a word list. It misses leading questions that
  use none of its words.
- Starters are picked oldest first, not by area. To change the order, switch
  off the ones to skip.
- Whether a Thought Experiment really tells its two Pattern Types apart is
  untested. The whole-pipeline Eval (issue 19) and real answers will show it.
