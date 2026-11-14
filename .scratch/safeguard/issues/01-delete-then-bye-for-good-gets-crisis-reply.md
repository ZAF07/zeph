# 01 — "DELETE" then "bye for good" gets the Crisis Reply

Status: ready-for-human

## Symptom

A User with a pending Delete My Data request sent "DELETE" and then "bye for good" within the Message wait. Instead of the normal reply (nothing deleted, the word only counts when sent on its own), they got the Crisis Reply with the Singapore Helplines straight away:

> I'm really glad you told me. I'm an AI, so I can't keep you safe the way a person can — but people are ready to help right now: Samaritans of Singapore (SOS): 1767 (24 hours) …

Expected: in context (they had just asked to delete their data and were leaving the Companion), this reads as saying goodbye to the app, not as a crisis. The reply should have been the normal one.

Impact: no crash. The User gets a Crisis Reply they didn't need, which can feel jarring or alarming at the moment they're leaving. The pending Delete My Data is cancelled (as on any crisis), and a Safeguard Event is saved. The Safeguard is meant to lean towards a false alarm when unsure (CONTEXT.md, **Safeguard**), so this may be the rule working as designed; the question is whether the check can tell these cases apart better.

It's unknown which label the model gave (a crisis label, or no label so it counted as unclear); the worktree database it ran in has been torn down. The Safeguard Event's risk type would say.

## Repro

Found during the `/run` for `.scratch/messages/issues/archive/03-delete-word-sent-on-its-own.md` (14 Nov 2026), in a worktree's running backend with the real app wiring and the real Safeguard model:

1. A connected, onboarded User asks to delete their data in chat (or `users.data_deletion_requested_at` is set).
2. They send "DELETE", then "bye for good", within `message_wait_seconds`.
3. Each text is saved and checked by the Safeguard as it arrives (`ReplyGate.screen` → `Safeguard.assess`). The check on "bye for good" sees the Conversation so far, with the User's texts in a row as one latest message ("DELETE\nbye for good"), and returns a crisis.

Not deterministic: it depends on the model's answer. In the same session, "DELETE" then "oh and is it going to rain today?" got the normal reply every time.

## Notes for the solution (needs `/grill-with-docs` first)

Don't pick a solution yet; grill it with the docs first (`CONTEXT.md` **Safeguard**, **Crisis Reply**, **Safeguard Event**; the Safeguard prompt and model settings).

- **Sort crisis possibilities into categories.** An idea is to have the check say not only "crisis or not", but how sure it is and what kind, e.g. clear crisis, ambiguous wording that could mean leaving or ending something ("bye for good", "I'm done"), or everyday distress. Each could get its own response, e.g. a gentle check-in question for the ambiguous case instead of the full Crisis Reply.
- **A better way to detect crisis than one model call.** Today every text is passed to one model with the Conversation as a transcript and one label comes back. Worth exploring: taking context into account on purpose (what the User was doing, like deleting their data or saying goodbye), more than one signal, or a second look before sending the Crisis Reply when the first answer is borderline. Any approach must still never miss a real crisis (CONTEXT.md: a false alarm is better than a missed crisis).

## Acceptance criteria

- [ ] Agreed approach recorded (from `/grill-with-docs`), with any ADR and `CONTEXT.md` updates
- [ ] "DELETE" then "bye for good" with a pending Delete My Data no longer gets the full Crisis Reply, while clear crisis messages still do
- [ ] Tests cover the fixed behaviour (and the Safeguard eval, if one covers it, still catches real crises)
- [ ] `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` pass
