# Patterns are tested by code against a Pattern Catalog

Status: accepted, built in part (what is built is listed in `docs/pattern-pipeline/README.md`). Replaces ADR-0020.

Under ADR-0020 the model wrote Patterns freely, and a User's "yes" to a Read confirmed one. That made Zeph's deepest claims about a person rest on a model's guess and on a reaction people give easily: they accept flattering reads and reject accurate ones that sting. We now test Patterns. Each is of a Pattern Type from a human-written Pattern Catalog; the model only reads what Users say into it, as Observations with an exact quote and tags from fixed lists; code checks the quotes, works out a score, and alone moves a Pattern between seven states (noticed, suspected, ready, shared, confirmed, contested, closed), logging every move. Only a ready Pattern is shared, with the User's own quotes and a Prediction they test in their own life. The flow is in `docs/pattern-pipeline/README.md`.

## Considered Options

- **A separate pipeline beside Patterns.** Rejected: two stores of what Zeph suspects about a User would compete, the reason ADR-0017 gave against a second store of guesses.
- **Gating the Read too.** Rejected: a Pattern takes weeks to become ready, so a new User would get only mirroring, which the 19 Nov 2026 review fixed. The Read is a view of one situation and is corrected in the moment; a Pattern is a claim about who someone is, so the gate sits there. The Read may still think with any Pattern in mind.
- **Look-alikes as rivals for the whole person** (share one only when ahead of the other by a margin). Rejected: a User can have both, and then neither is shared. Look-alikes compete per Observation instead: one the model can't place is unclear and counts for little toward each, and a Pattern is ready only on clear evidence.
- **A probability.** Deferred: the catalog's numbers are placeholders, so the result is a score used to rank and compare. Users never see a number. It becomes a probability once Prediction outcomes show it is calibrated.
- **Only catalog Patterns exist.** Rejected: fifteen Pattern Types miss most of what people show. What recurs and fits none is kept as an unmatched Pattern, hidden and never shared, usable by the Read, and listed for Admins without User details so the catalog can grow.

## Consequences

- A User's agreement is supporting evidence that adds up; code confirms, on Predictions that came true. A rejected Pattern is contested: never offered again unless the User raises it, with evidence still gathered silently while the User's own switch allows.
- A situation is one Life Thread; the same way shown with different people within it adds weight, up to a cap. A Pattern needs several situations across more than one Conversation.
- Users see a Pattern only once Zeph has told them about it, which keeps ADR-0020's reason (a cold read on a page lands like a horoscope) and stops them answering Zeph's questions knowing what it looks for.
- Curiosities may now be made to check a Pattern (ADR-0026), which ADR-0020 ruled out.
- Patterns the live User already has are kept: confirmed ones stay confirmed and visible, suspected ones become unmatched, and each is matched to a Pattern Type where one fits. A match is a link from the old Pattern to the Pattern Type, not a change of the Pattern: its words, state and evidence stay, and the Conversations behind its evidence are tagged again so a Pattern of that Pattern Type grows from checked Observations. Making the old Pattern itself the Pattern of the Pattern Type was rejected: it has no Observations, so scoring would delete or close it.
- Rollout is three Features, each needing the one before: Pattern noticing, Pattern exploring, Pattern sharing.
