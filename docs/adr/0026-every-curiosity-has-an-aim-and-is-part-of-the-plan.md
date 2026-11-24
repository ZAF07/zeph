# Every Curiosity has an aim and, once picked, is part of the plan

Status: accepted, not built yet. Amends ADR-0017.

Zeph was passive: with the live limits at 5 Curiosities per Conversation and 7 Curiosity Check-ins a week, it still raised almost nothing that mattered. The cause was not the budget. A Curiosity could be dropped twice (the Reply Plan was told to leave it out unless the moment was right, then the Reply got it as an optional extra), it lost to every other question, and a model wrote it with nothing to aim at. We keep Curiosities as the one store of things to ask, and change their standing: each has an aim, code writes and ranks the ones that serve a Pattern, each Need says how Curiosities are treated while it is picked, and one the Reply Plan picks is part of the plan the Reply follows.

## Considered Options

- **Separate "probe" tables for Pattern questions**, as the source design had. Rejected: two question queues would compete for the same reply. Curiosities already carry the state, sensitivity and how the User took it.
- **A separate budget for Pattern questions.** Rejected: one module, one budget.
- **Raising the limits.** Already tried in production; it changed nothing.

## Consequences

- An aim is something an Exploration needs (an unclear story, a missing part of life, a counter-test), a Prediction or commitment to follow up, a look-back, or a guess to check. A Curiosity with no aim is never made.
- Zeph keeps an Agenda: a User's active Explorations, each remembering every try and what came back, so it can return to a need days or weeks later a different way.
- Each Need gets an Admin-set field: Curiosities asked by default, tested lightly, only if they fit, or never. Just chatting starts as tested lightly, so banter stays banter.
- Pace and backing off are code with Admin-set numbers: a fewest replies between two Curiosities, a cap on follow-ups to a story being told, and a pause after brush-offs in a row that one engaged answer ends.
- ADR-0017 still holds: a guess about a single fact is a Curiosity and never User Memory.
- This part needs no Pattern Catalog, so it is built first.
