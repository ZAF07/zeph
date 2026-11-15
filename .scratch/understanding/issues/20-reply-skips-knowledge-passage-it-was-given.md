# 20 — Reply sometimes skips a Knowledge passage it was given

Status: ready-for-agent

## What

Seen while closing bug 16 (2026-11-14). With bug 16 fixed, the Knowledge eval with `RunningClock` still misses a step now and then (2 of 6 runs, 1 step each). The Understanding chose the right document and its passage reached the reply's instructions, but the reply didn't use it.

So the Understanding is fine here; the likely place is the reply prompt (how passages are introduced in `reply_knowledge_intro`, and the persona), but that isn't confirmed yet. Split out of issue 17, which tunes only the Understanding.

## First step: find the cause

Run the Knowledge eval until a step fails, open that step's trace in the Model Call Log, and say which of these it is before changing anything:

- The reply prompt doesn't push the reply to use a passage it was given.
- The passages found weren't the part of the document that answers the question (search phrase or closeness bar).
- The Judge is too strict: the reply did use the passage, in its own words.

Each needs a different fix; record the one found under `## Comments`.

## Repro

```sh
set -a && . ./.env && set +a
uv run pytest -n 0 evals -m eval -k knowledge
```

Run it a few times; a failed step's trace in the Model Call Log shows the passage in the reply call's instructions.

## Acceptance criteria

- [ ] The Knowledge eval passes 3 runs in a row
- [ ] The other Evals don't get worse
- [ ] `make check-python` passes

## Working alongside issue 19

Not blocked: this can run while `19-understanding-picks-knowledge-by-number.md` is in flight.

- The diagnosis can start now.
- A fix to the reply prompt (`reply_knowledge_intro`, the persona) or the Judge can go ahead; issue 19 edits `understanding_prompt`, so they don't clash.
- If the cause is the passages found (the search phrase in `understanding_prompt`), wait for issue 19 to merge first.
- Either way, rebase on issue 19 before the final "3 runs in a row" check.

## Comments

- 2026-11-15 diagnosis: **the reply prompt doesn't push the reply to use a passage it was given.** Baseline 4 runs: 1 failed step (pebble-practice, "details edited"), 3 runs clean. In the failed step the Understanding chose “The Windowsill Book” and the right passage reached the reply's instructions under `From “The Windowsill Book” (Recorded by Elder Bramwell Osk, Fenmoor Hermits)`. The reply answered "I don't have a real teacher or book to point to for it. The version in my library is credited to a fictional hermit". The intro said "Most of the time, use none of them. Draw on one only if it genuinely fits what the person is going through", so a plain "where does it come from?" question didn't count as a fit, and the model fell back on its own knowledge. The passages found were right and the Judge was right (the reply named no source). Fix: `reply_knowledge_intro` now says to answer from the passages, with their details and source, when the person asks about a practice or teaching there or where it comes from; otherwise keep the old light touch. The Understanding already decides when Knowledge fits, so the reply no longer second-guesses it for direct questions.
