# 01 — A Curiosity-keeping Eval

Status: needs-triage

> **When you pick this up, start with `/grill-with-docs`.** The shape of this Eval (cases, what the Judge checks, how a finished Conversation is given) isn't decided yet.

## Why

The Get curious work (grilled 2026-11-18) changes what the Curiosity-keeping step writes when a Conversation ends:

- a **look-back Curiosity** for a vent where Zeph only listened, with `not_before` at least the next day;
- a **guess**: something Zeph suspects about the User but isn't sure of, with how sure it is, closed once the User answers.

There is no Eval for the Curiosity-keeping step today, so these are checked only by `/run` on a real Conversation end. That work chose not to build the Eval yet, since a new kind of Eval is bigger work (a new case shape, ADR-0014).

## Rough idea

Like the Move Outcome Eval: give a finished Conversation (and the User Memory, Life Threads and waiting Curiosities it needs), run the real Curiosity-keeping step on it, and check the Curiosities it writes, updates or closes.

Starting cases to consider:

- A Conversation where Zeph only listened to a vent → a look-back Curiosity, `not_before` at least tomorrow, sensitivity at least medium.
- The User hints at a fact without settling it → a guess, with how sure Zeph is.
- The User answers a waiting guess → it is closed, and the fact isn't written as a new guess.

## Acceptance criteria

To be set after `/grill-with-docs`.

## Comments
