# 03 — Get curious Move and the venting line

Status: ready-for-agent

## Parent

`.scratch/get-curious/PRD.md`

## What to build

A new Move, **Get curious**, lets Zeph get to know the User: one natural question about something they just said, to learn something new about them, go a little deeper, or check something it isn't sure of.

- **Seed Move.** Its "when it fits" covers the User mentioning something about their life (plans, people, sleep, routines, work) that Zeph knows little about, half-knows, or isn't sure it has right. Its "how to do it" says:
  - ask one short, light question about something they just said, the way a curious friend would;
  - prefer what Zeph doesn't know yet, or a guess it holds;
  - checking something it thinks it knows is fine when it isn't sure;
  - it can be practical and kind ("you a coffee person?"), never a quiz;
  - let it go after a short answer.

  It needs no Feature, and "asks a question" (issue 01) is ticked.
- **Needs.** Ask more and Get it done rule it out; the other Needs allow it.
- **The venting line.**
  - Be heard's "when it fits" becomes roughly: "They're letting out something painful or frustrating, staying on it or coming back to it, often with strong words, and want it to land with someone, not to be fixed… A hard thing mentioned in passing (tired, busy day, a small annoyance) is not this: that's an update." Keep its existing Goal-slip sentence.
  - Just chatting's "when it fits" adds "including passing mentions of everyday hard things, like poor sleep or a long day."
- **Running platform.** The migration:
  - adds Get curious only if no Move with that name exists, ignoring case, placed last, with the box ticked;
  - adds the rule-outs to Ask more and Get it done if they still exist;
  - updates the Be heard and Just chatting wording only where it still matches the old seed word for word.

  The seed files get the same changes.
- **Evals.** Two new Understanding Eval cases in the seed. **Don't run them**; Evals cost money and the owner decides when.
  - The passing update: after a morning Check-in, "It's going to be a long day" then "5 hours sleep only". Expect Just chatting, with Get curious as lead or supporting.
  - A real vent: "ugh I'm so done, my boss tore my work apart again in front of everyone". Expect Be heard, and no question about why they feel it.

## Parallel work: avoid clashes

Issue 04 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 04 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Files:** you own the Needs and Moves seeds. 04 owns the Curiosity-keeping and Portrait prompts in the platform settings seed.
- **Understanding Eval cases seed:** both add cases at the end. When rebasing, keep both.

## Acceptance criteria

- [ ] Get curious is in the Moves seed with "asks a question" ticked; a new install has it, ruled out by Ask more and Get it done and allowed by the rest
- [ ] Be heard and Just chatting seed wording draw the venting line as above
- [ ] The migration adds Get curious with its rule-outs to an existing database, and leaves one that already has a "Get curious" Move as it is
- [ ] The migration updates unchanged Be heard and Just chatting wording and leaves edited wording alone (migration test, as in the Moves migration test)
- [ ] Get curious is offered to the Understanding under Just chatting and not under Ask more (webhook test)
- [ ] The two Understanding Eval cases are in the seed and load (seed loading test); they are not run
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] `/run`: after the migration, the Dashboard Moves page shows Get curious with the box ticked and the Needs pages show the new rule-outs and wording. In the running app, sending "It's going to be a long day" / "5 hours sleep only" gets an Understanding of Just chatting with Get curious, and a reply with one natural question (one real Message, not an Eval Run)

## Blocked by

- `.scratch/get-curious/issues/01-asks-a-question-checkbox-on-moves.md`

## Comments
