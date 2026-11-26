# Conditions narrow a Pattern; they are never counted, and never asked for to fill a blank

Status: accepted (pattern-pipeline issue 23). Built so far: the Conditions are tagged, checked and stored (issue 41), "anyone would" can match them (issue 42), and Zeph asks about a missing Condition (issue 43). Not built: narrowing and sharing (issue 44). Builds on ADR-0024.

Zeph follows Mischel and Shoda (1995): a person is known by their "if situation, then behaviour" signature, and the situation that matters is what it means to them (who was there, what was at stake), not the room or the clock. Until now an Observation's tags, and so a Pattern's narrowing and Zeph's questions, varied almost only the person. We now tag more Conditions (audience, stakes and the User's state going in, beside relationship, power, stance and setting) and use them for one job: to say when a Pattern Type's "if" sets the Pattern off for this User and when it doesn't ("with people above you, in a group; not one-to-one"). The owner's aim is self-awareness, not proof: the rules below keep what Zeph claims honest and keep it from interrogating. Every decision, with its reason, is in `.scratch/pattern-pipeline/issues/23-situations-vary-on-more-than-people.md` (archived when built).

## Considered Options

- **Tag the whole situation, event included, to find patterns the catalog lacks.** Rejected: that is finding new Pattern Types, which is parked. A Pattern Type's "if" already names the event, so an event tag would repeat it.
- **A time tag (time of day, day of week).** Rejected: stories rarely give one, and when time matters it stands in for state ("late at night" means worn out). State is tagged as of when the story happened, from the story's own words.
- **State read from the Understanding or a Day Summary.** Rejected: that is how the User seemed while telling the story, not how they were when it happened, and it would keep something they never said.
- **A different mix counts as a different situation** (tired and rested as two). Rejected: richer tags alone would make Patterns ready sooner on the same evidence. A situation stays one Life Thread, and the cap inside it stays per person.
- **Ask whenever a Condition is empty.** Rejected: that is interrogation. A Condition is filled only when the story says it. Code asks about an unseen value only for a suspected Pattern whose stories so far are one-sided, one Condition at a time, inside the existing question limits.
- **Narrow on any Condition that differs, or on stored combinations.** Rejected: with seven Conditions almost any story against differs on something, so all evidence against would be explained away; combinations need more stories than a User gives. Each Condition narrows alone, needs at least two clear stories on the side that holds, and at most two narrow one Pattern.

## Consequences

- Conditions never add to a Pattern's score or its situations. They narrow it, and they may mark an Observation as one where anyone would act the same (high stakes, for two Pattern Types that couldn't say so in tags before).
- Zeph learns Conditions slowly, and nothing is asked about them while a Pattern is only noticed. Zeph will sometimes claim less than the evidence could support.
- When a Pattern is shared, Zeph also says one thing it hasn't seen, as an open question and never a claim, so the User can notice it for themselves.
- State is sensitive: it is kept only from the User's own words, in everyday terms, goes with its quote, is never shown to Admins, is never tagged in a Conversation with a Safeguard Event, and Zeph never names a state the User hasn't said.
- The lists are short on purpose, so a trend can show from a handful of stories. Lists and bars are first guesses and easy to change; the rules above are not, since every Observation stores its Conditions and the Pattern Catalog's "anyone would" rules point at them.
