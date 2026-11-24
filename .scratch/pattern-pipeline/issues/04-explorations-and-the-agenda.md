# 04 — Explorations and the Agenda: Zeph knows what it is trying to learn and comes back to it

Status: ready-for-agent
Track: A
Blocked by: 01, 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 2, 3, 4, 5, 7, 29). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Zeph needs to remember what it is exploring. An Exploration is its ongoing effort on one suspected Pattern: what it still needs to learn (an unclear story to settle, a part of the User's life it hasn't seen, a counter-test), each try (which Curiosity, when, whether what came back was useful, vague or brushed off), and what to try next and not before when. The Agenda is the User's active Explorations, at most an Admin-set number (start 3), ranked by code.

After scoring at Conversation end, code keeps the Agenda and writes the next aimed Curiosity for each Exploration, least pushy way first: a follow-up on a story, "would it have gone differently with…", then (issue 05) a Thought Experiment, then "this week, notice when…". A try that gets nothing useful leaves the need open. An Exploration is never worked on two Conversations in a row, waits after a try with nothing (start 3 days), rests after tries with nothing (start 4) and wakes on new evidence. The Reply Plan sees the Agenda with each Exploration's earlier tries on every reply, and Get curious is aimed by its open needs. All behind a new Feature, Pattern exploring, which works only when Pattern noticing does.

## Acceptance criteria

- [ ] A suspected Pattern gets an Exploration with its open needs worked out by code from its Observations (unclear, missing part of life, counter-test)
- [ ] At most the Admin-set number of Explorations are active for a User, ranked by code
- [ ] Code writes an aimed Curiosity for an Exploration's top need; the model only words it
- [ ] Each try is saved with its Curiosity, when it was asked and how it went
- [ ] A try that came back vague or brushed off leaves the need open, and the next try uses a different way after the Admin-set wait
- [ ] The same Exploration is not worked on in two Conversations in a row
- [ ] An Exploration rests after the Admin-set number of tries with nothing, frees its place, and wakes when a new Observation arrives for its Pattern
- [ ] The Reply Plan is given the Agenda with earlier tries, and Get curious is given the open needs
- [ ] An answer to an aimed Curiosity that settles an unclear Observation is tagged as clear at Conversation end
- [ ] With Pattern exploring off for a User, no Explorations or aimed Curiosities are made and none are deleted
- [ ] Delete My Data and Account Deletion remove Explorations
- [ ] Agenda ranking and the Exploration rules are pure functions with their own tests; every number is a Platform Setting with a hint
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`
- `12-patterns-scored-and-moved-by-code.md`

## Comments

Plan (24 Nov 2026, branch `pattern-04-explorations`, worktree `ai-chat-companion-pattern-04`):

- **Feature Pattern exploring**, off to start; works only while Pattern noticing works (a general "needs Feature" rule beside the Stickers one, with its own reason).
- **Store.** `explorations` (one per User and Pattern, goes with its Pattern): state active (on the Agenda), waiting (for a place, or its Pattern isn't suspected) or resting; when it rested and woke. `exploration_tries`: one per aimed Curiosity (its question and when it was asked come from the Curiosity), with the need, the way, the Observation or part of life aimed at, and the outcome (useful, vague, brushed off). Curiosities get the aim `exploration`, plus `exploration_id` and `source_observation_id`, so deleting the Exploration or the Observation deletes its waiting Curiosity (like Threads and Memory Items today).
- **Open needs, worked out by code from the Pattern's Observations** (pure): unclear (each unclear Observation, newest first), missing part of life (home, work or with friends: one with no Observation while another has one), counter-test (no Observation against yet and no useful counter-test try). Top need is the first in that order.
- **Ways, least pushy first:** story follow-up → "would it have gone differently with…" → "this week, notice when…" (Thought Experiments slot in with issue 05). Each try with nothing moves that need to the next way, round again after the last.
- **Outcome, decided by code from the reaction:** brushed off or asked to drop → brushed off; engaged and a new Observation of its Pattern Type came from that Conversation (or its unclear Observation is now clear) → useful; otherwise vague.
- **Agenda step** at Conversation end, after Curiosities, while Pattern exploring works (User locked, like scoring): save the outcome of every aimed Curiosity asked in the Conversation; give each suspected Pattern an Exploration; wake resting ones with a new Observation since they rested; rest one after `exploration_rest_after_tries` (4) tries with nothing in a row, or at once when asked to drop; rank the rest by score (highest first, then oldest) and put the top `agenda_size` (3) on the Agenda; close the waiting aimed Curiosity of any that leave it. For each active one with no waiting aimed Curiosity, not tried in this Conversation (so never two in a row), code writes one for its top need with the next way, not before the last try's day + `exploration_wait_days` (3) after a try with nothing.
- **Wording.** Code writes the Curiosity's question as a plain instruction from the Observation's day and context line, the Pattern Type's "if" and a part of life ("Go back to what they told you on 3 Nov (…): ask what they did next and what they hoped wouldn't happen"); the Reply words it as today. No Pattern name reaches the Reply.
- **Reply Plan** gets the Agenda each reply while Pattern exploring works: each Exploration (Pattern Type name, marked never to say), its open needs and earlier tries (day, way, question, outcome), and a line saying Get curious aims at an open need. Aimed Curiosities come first among the due ones, and are offered only while Pattern exploring works. The Curiosity keeping model never sees or closes waiting aimed ones.
- **Settling unclear.** The tagging step is shown the aimed Curiosities asked in the Conversation that aim at an unclear Observation, and may answer `settled` with the Observation's number, the Pattern Type and a sign; code accepts only one of its two Pattern Types and a sign of that type in the same direction, and makes the Observation clear. Prompts for tagging and the Reply Plan are reloaded from the seed (migration).
- **Off:** nothing made, nothing deleted, no Agenda in the Reply Plan, aimed Curiosities not offered.
- **Deletion:** Delete My Data and Account Deletion remove Explorations and tries.
- **Settings** in the Patterns section with hints: `agenda_size` 3, `exploration_wait_days` 3, `exploration_rest_after_tries` 4; overridable in Eval Variants.
- **Tests:** pure tests for needs, ways, outcomes, ranking and the Agenda plan; HTTP-edge tests for the Conversation-end chain, the Reply Plan input, Feature off and deletion.
