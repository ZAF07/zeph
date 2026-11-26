# 44 — Narrowing and sharing use every Condition

Status: ready-for-agent
Track: A
Blocked by: 41, 43 (43 builds the coverage table this issue reads)

## Parent

Issue 23, decisions D9, D10 and D11 (point 3), and the owner's principle there. ADR-0031. Today's rules: `narrowings_of` in `core/pattern_scoring.py`, "the ready gate", "sharing a ready Pattern" and "the Patterns tab" in `docs/pattern-pipeline/README.md`.

## What to build

A Pattern can be narrowed by any Condition, with guards so it can still be shown wrong. When it is shared, Zeph also says one thing it hasn't seen.

- **Narrowing (`narrowings_of`):**
  1. each Condition is looked at alone; no combinations;
  2. a Condition narrows only when at least `narrowing_stories_needed` (2) clear stories for have it known on the side that holds, and the clear evidence against is all with other values (today's rule, with the bar raised from 1);
  3. at most `narrowings_per_pattern` (2) narrow one Pattern: those with the most stories behind them, ties by a fixed order of Conditions;
  4. evidence against that the kept narrowings don't explain counts against the Pattern in full.
- **Where it shows** (the gate's other-side call, sharing, the Patterns tab): every kept narrowing in plain words for each Condition ("in a group; not one-to-one", "when a lot is riding on it"). For state, gentle words about the moment ("on days you were worn out"), never a label for the User.
- **One thing not seen, when sharing:** code hands the reply at most one gap from the coverage table (the open missing-Condition need of issue 43, read from its coverage table; build no second version of that rule), to say as something Zeph doesn't know ("I've only heard about this in meetings. I don't know if it's the same when it's just the two of you"), never as a claim. A state gap is never handed over, since Zeph never names a state first. The reply that shares still asks nothing else beyond "what would prove it wrong".
- **The Prediction** is unchanged, set inside the narrowing as today.
- **Scoring:** Conditions never add points or situations; a situation stays one Life Thread and the cap stays per person. Add tests that say so.
- **Numbers:** `narrowing_stories_needed` and `narrowings_per_pattern` are Platform Settings with hints in the Patterns section, overridable in Eval Variants.
- **Copy:** new words for the Patterns tab are Copy slots (`memories.patterns.*`); UI work follows `web/design/README.md` and the pixel test.

## Acceptance criteria

- [ ] A Condition narrows only with at least 2 clear stories for on the side that holds; one story no longer narrows
- [ ] With three Conditions able to narrow, only the two with the most stories do, and evidence against that those don't explain counts against the Pattern
- [ ] Evidence against that a kept narrowing explains is not counted against the Pattern, as today
- [ ] Two Observations in one Life Thread with different Conditions count as one situation, and the cap inside it is per person
- [ ] The ready gate's other-side call, the shared Pattern and the Patterns tab show each kept narrowing in plain words, state in gentle words
- [ ] A sharing reply is handed at most one unseen value, marked to be said as not known; never a state; none when nothing is one-sided
- [ ] The Prediction is still set inside the narrowing
- [ ] The two numbers are on Platform settings with hints and can be overridden in an Eval Variant
- [ ] `docs/pattern-pipeline/README.md`, `lifecycle.md` and the `CONTEXT.md` Pattern entry say what is built
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass; `pnpm lint`, `format:check`, `typecheck` and `test` pass for any Dashboard change, with the pixel test
- [ ] Checked in the running app (`/run`): a Pattern seen in a group and shown not to happen one-to-one is shared with that narrowing, the reply says one thing Zeph hasn't seen, and the Patterns tab shows where it shows

## Comments
