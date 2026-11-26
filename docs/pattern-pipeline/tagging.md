# Tagging

How Zeph turns what a User said into **Observations**, and what else the same model call reads. For what happens to an Observation afterwards (scoring, states), see `lifecycle.md` in this folder.

The rule throughout: **the model reads, code decides.** The model writes a JSON answer, and code keeps only what passes its checks.

Code: `PatternTagger` in `src/companion/core/observations.py`. The checks are pure functions in the same file.

## When it runs

At every Conversation end, after the Life Thread step and before scoring (`_tag_observations` in `src/companion/core/post_conversation.py`).

It runs only when all of these are true:

- User Memory and the Feature **Pattern noticing** work for the User.
- The User has pressed "Got it" on the notice saying Zeph keeps some of their words (`may_keep_observations`).
- The User wrote something in their own words in the Conversation.
- The catalog has at least one Pattern Type.

A failure is logged and never stops the other Conversation-end steps.

## What the model is given

One model call (`describe_conversation_to_tag` builds the input):

| Input | Why |
|---|---|
| Today's date | To place stories in time |
| The Life Threads the Conversation touched, numbered | So an Observation can be linked to its Thread |
| Every Pattern Type in the catalog: definition, signs for and against with strength, look-alikes, what anyone would do, exclusions | What to tag against |
| The fixed lists of the seven Conditions and the kinds of evidence | Tags must come from them |
| The Conversation | What to read |
| Unclear Observations Zeph asked about in it, numbered | So the model can settle them |
| Thought Experiments put to the User in it, numbered | So an answer is marked as a "what if" answer |
| The User's open Life Threads and latest Day Summaries (7 days) | To say which exclusions apply now |
| The Admin-set ruled-out topics | To mark an Observation on one |
| Patterns Zeph has told the User, numbered | To read how they took them |
| Their open Predictions, numbered | To read how they went |

Settings: `pattern_tagging_prompt`, `pattern_tagging_model`, `pattern_tagging_thinking`. The prompt holds no numbers.

## What the model answers

One JSON object with five parts:

| Key | What it holds | Kept by |
|---|---|---|
| `observations` | The Observations it found | `plan_observations` |
| `settled` | Which Pattern Type an unclear Observation really is | `plan_settled` |
| `exclusions` | Exclusions that apply to the User now | `plan_exclusion_flags` |
| `reactions` | How the User took a Pattern they were told: agreed, pushed back, brushed off | `plan_reactions` |
| `prediction_outcomes` | How an open Prediction went: came true, didn't, hasn't come up | `plan_prediction_outcomes` |

If the answer can't be read (no `observations` list), it is asked once more. If it still can't be read, nothing is kept.

### One Observation as the model writes it

- Pattern Type (one, or two when it can't tell look-alikes apart: **unclear**)
- Sign, and for or against
- The exact quote
- A context line on what was going on
- Who it was about
- Life Thread number (optional)
- Conditions: relationship, power, setting, stance, audience, stakes, state going in (each from its list, or empty)
- Kind of evidence
- Thought Experiment number, if it answers one
- Ruled-out topic, and whether the User raised it

## The checks

`check_observation` drops an Observation for the first reason that applies:

| Drop reason | When |
|---|---|
| Not an Observation | It isn't a JSON object |
| Unknown Pattern Type | A Pattern Type it names isn't in the catalog |
| Never again | It names a Pattern Type the User marked "never again", by deleting a Pattern they disagreed with or that didn't hold up |
| Not gathered | It names a Pattern the User disagreed with, while they have "Keep noticing after I disagree" off |
| Unknown sign | Its sign isn't in the first Pattern Type's signs for (or against, if it's against) |
| Quote not word for word | The quote isn't in one of the User's own texts |
| Deleted by the User | The quote shares words with one the User deleted from this Conversation before (matched by a hash of the message and the quote's place in it; the words aren't kept) |
| Tag off its list | A Condition or the kind of evidence isn't from its list. An empty Condition is fine |
| Missing details | No context line, or no one it is about |
| Repeat | Same Pattern Type, sign and quote as one already kept from this answer |

**The quote check** (`find_quoted_text`): the quote must be inside one of the User's texts (text messages and photo captions only, never Zeph's texts or a photo's description), starting and ending on whole words. Only runs of spaces and curly quotes are evened out. A quote can't span two texts.

How many were tagged and dropped goes into the Model Call Log (`tagging_shape`). The User's words never do.

## The Conditions

A **Condition** says under what circumstances a story happened. All seven come from closed lists in `core/models.py`, and `describe_tag_lists` writes the lists into the model's input from those enums.

| Condition | Values | Filled when |
|---|---|---|
| relationship, power, setting, stance | See the enums | It is clear from the Conversation |
| audience | one-to-one, group, in front of others (people watching who aren't part of it) | The User's own words say it |
| stakes | low, high (something that matters to them could be lost) | The User's own words say it |
| state going in | worn out, under pressure, low, steady | The User's own words say how they were **before** it happened |

Rules for audience, stakes and state going in (ADR-0031):

- **Never guessed.** Not said means empty. The prompt says so, and the Tagging Eval has "must be empty" cases.
- **One value each.** When a story gives two, the one it leans on; empty when the model can't tell.
- **State is before, not after.** "I was shattered after" leaves it empty. It is never read from how the User seems while telling the story.
- **No state after a crisis.** When the User had a Safeguard Event at or after the Conversation's first message, code empties state on every Observation from it, whatever the model wrote (`had_safeguard_event`).
- **Private.** They are stored on the Observation's row and go when it goes. "Things you said that Zeph kept" and the Admin pages show none of them.

Nothing reads audience, stakes or state going in yet (issues 42 to 44).

## What code adds to a kept Observation

| Field | How it is set |
|---|---|
| Day | The day the quoted text was sent, in the User's time zone |
| Life Thread | From the number, or none if it names a Thread it wasn't shown |
| Kind of evidence | Forced to "what if" answer if it names a Thought Experiment asked in the Conversation |
| Situational | True when its tags fit one of the Pattern Type's `anyone_would_when` matches (`is_situational`). It then counts nothing |
| State going in | Emptied when the Conversation had a Safeguard Event |
| Excluded | True when an exclusion with `ignored` evidence applies to one of its Pattern Types now. It then counts nothing, ever |
| Ruled-out topic | Kept only if the topic is on the Admin list |
| Pattern Type versions | The catalog version at tagging time |

The quote is stored on the Observation with no link to its message, so Message Retention never deletes it.

## The other four parts

- **Settled.** An unclear Observation becomes clear when the model names one of its two Pattern Types and a valid sign. Situational is worked out again for that Pattern Type.
- **Exclusions.** Code keeps one only when that Pattern Type lists it. Each tagging replaces the User's flags (`pattern_exclusion_flags`). While a flag applies, its Pattern is never ready.
- **Reactions.** One per Pattern and Conversation. A shared Pattern the User pushed back on is made **contested** right after tagging (`settle_reactions` in `pattern_sharing.py`).
- **Prediction outcomes.** One per Prediction shown. "Came true" and "didn't" count as strong evidence for and against. "Hasn't come up" starts a new wait.

## Tagging a past Conversation again

`tag_again` re-tags an old Conversation against some Pattern Types only. It is used by `PatternMatcher` (`src/companion/core/pattern_matching.py`), an Admin command run when a Pattern Type is added. When an unmatched Pattern matches the new Pattern Type, its old Conversations are tagged again so the evidence becomes real Observations.

The differences from a normal tagging:
- It uses only the messages still kept, since Message Retention may have deleted some.
- It skips any Observation already kept from that Conversation.
- A quote the User deleted is never kept again, and nothing is kept for a Pattern Type they marked "never again" (the same checks as any tagging).
- It doesn't touch exclusions, reactions, Predictions or settling.
- State going in is emptied when the User had a Safeguard Event at any time since the first message still kept from that Conversation, not only in it. If Message Retention deleted the messages around a Safeguard Event, a state may be kept.
- New Observations are scored at once (cause `evidence_tagged_again`).

## Testing it

- Unit tests cover the pure checks (`plan_observations`, `check_observation`, `plan_settled` and the others).
- The **Tagging Eval** runs the real model on made-up Conversations and checks the Observations it keeps. It costs money. See `docs/pattern-evals/README.md` and `docs/pattern-evals/adding-tagging-cases.md`.

## Limits

- Time of day and kind of event aren't tagged, on purpose (ADR-0031).
- Audience, stakes and state going in can make an Observation situational (a match may name them, issue 42), but they don't narrow a Pattern or aim a question until issues 43 and 44.
- Only some Pattern Types have `anyone_would_when` matches. A match fits only a tag the Observation holds: a high-stakes story where the User never said what was at stake has stakes empty and is not situational.
- Observations kept before issue 41 have no stakes tag, so they never fit a high-stakes match and keep their weight.
- A topic added to the ruled-out list doesn't reach Observations tagged before.
- An exclusion flag stays until the User's next tagged Conversation.
- A story that settles a Prediction is still tagged as an Observation, but it counts nothing for that shared Pattern (the outcome keeps its Conversation in `predictions.outcome_conversation_id`).
