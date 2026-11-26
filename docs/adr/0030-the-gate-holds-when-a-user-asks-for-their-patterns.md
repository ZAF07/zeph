# The gate holds when a User asks what patterns Zeph sees in them

Status: accepted (the owner, 25 Nov 2026). Built: pattern pipeline issue 39.

Two rules met head on. The **Read** is free: Zeph forms a view of what is going on in every reply and may say it. The ready gate is strict: code decides which Pattern may be claimed about who a User is (ADR 0024). In the running app, a User who asked "what patterns do you see in me?" while their Pattern was only suspected got it stated anyway, with named people, no Prediction and nothing recorded. A line in the Reply Plan prompt softened other replies but not this one.

The gate wins. When a User asks, only a Pattern that passed the gate is told:

- a ready Pattern that code offered is shared then and there, properly: quotes, a Prediction, recorded;
- else a Pattern Zeph already told them (being tested or confirmed) may be recalled, and no other;
- else Zeph says it is still getting to know them. It may give its view of one recent situation, as about that situation only.

The Reply Plan model reads whether they asked (`asked_for_patterns`); code picks which of the three applies and gives the Reply a fixed section for it. The Read stays free for everything else.

## Considered Options

- **Leave it: the Read is free.** Rejected: a User who asks gets an untested claim about who they are, which is exactly what the gate exists to stop, and the Patterns tab shows nothing for it.
- **Stop showing the Agenda's if / then to the Reply Plan.** Rejected: the Read builds the claim from Life Threads as well, so it wouldn't stop it, and aimed questions would get worse.
- **A rule in the prompt only.** Tried (issue 08) and it didn't hold when the User asks outright.

## Consequences

- A curious User may hear "I'm still getting to know you" for weeks. That is the honest answer, and the Agenda is what shortens it.
- Whether they asked is a model's reading. A miss leaves the reply as it was before.
- With an Admin-edited `reply_plan_prompt` kept on deploy (ADR 0029), the field is never filled until the new text is merged in by hand.
- Once a Pattern is told, replies are shown it and may name it, so Zeph uses what it learned instead of going quiet about it.
