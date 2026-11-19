# Suspected Patterns live with the Pattern, not as Curiosities

ADR-0017 keeps every guess about a User as a Curiosity and rules out a second store of guesses. A Pattern (a recurring way a User thinks, feels or acts across parts of their life) is an exception: we keep suspected Patterns as Patterns, hidden from the User, and let the Companion form its read from them, offered only as its view, never as fact. In a real Conversation the read that finally helped ("the PM, the project and the impatience with your mum are the same thing") was a suspected Pattern; under ADR-0017 the Companion could not have used it until the User confirmed it, and a Curiosity is a one-off question that is asked once and closed, while a Pattern must gather evidence across many Conversations and be thought with every time a linked Life Thread comes up.

## Considered Options

- **Suspected Patterns as Curiosities with a guess (ADR-0017 unchanged).** No new kind of guess, but the Companion can't think with a Pattern until it is confirmed, and evidence can't build up on a question that closes once asked.
- **All Patterns visible to the User.** Simplest, but shows half-formed beliefs about a person as if known, the harm ADR-0017 exists to prevent.
- **Confirming suspected Patterns on the Dashboard** ("Things Zeph thinks it's noticed. Is this you?" with "That's me" / "Not me"). Deferred, a possible future Feature: a read shown cold on a page, away from the moment it is about, can land like a horoscope or a judgment, so we start with confirming only in chat. Worth revisiting if too few Patterns get confirmed.

## Consequences

- ADR-0017 still holds for single guessed facts ("their mum lives in Singapore"); only Patterns carry their own sure-ness.
- A suspected Pattern is checked by offering the read; the User's reaction confirms or closes it. No Curiosity is made to check a Pattern, so one guess never lives in two places.
- Users see only confirmed Patterns; Delete My Data and Account Deletion remove all of them.
