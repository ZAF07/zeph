# 31 — Bring the Tagging Eval up to date, then fix what it shows

Status: ready-for-human
Track: shared
Blocked by: none (the owner's correction of the drafted cases comes first, see step 1)

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (sections 07, 09, 11 and 14), triaged with the owner on 25 Nov 2026. What the Eval can and can't show: `docs/pattern-evals/README.md`.

## Why

The Tagging Eval is how we know the tagging step is right, and today it can't be trusted:

- The first run passed 33 of 44 (run `4352910b`): "anyone would" moments kept nothing, a parent counted as "anyone would", look-alikes were rarely marked unclear, and CTRL "real crisis" cases were tagged the wrong way.
- The first 44 cases were written for 3 Pattern Types; the catalog now has 15, and several cases fit a new look-alike. The 24 newer cases have never been run.
- The tagging prompt has since learned exclusions, ruled-out topics and Prediction outcomes. No case checks them and no run was made after those changes.
- All cases are Claude's drafts. The score measures the step against Claude's labels, not the owner's.

## What to do

Evals cost money: show the owner the estimate and get a go-ahead before every run. The whole catalog goes into each call now, so a run costs several times the first one (S$0.15).

1. **Owner (human step):** correct the drafted Tagging cases, following `docs/pattern-evals/adding-tagging-cases.md`: correct on the Dashboard, run, then have an agent copy the cases into the seed. This ticks the open box in issue 20, section 14. Once done, set this issue to `ready-for-agent`.
2. **Agent:** run the Tagging Eval once on all 68 cases. Where a case now fits a new look-alike, change its expectation to "unclear" with the right pair, and ask the owner where it isn't clear.
3. **Agent:** add cases for what has none: grief, a job loss, a ruled-out topic raised by Zeph and one raised by the User, and Prediction outcomes (came true, didn't, nothing said).
4. **Agent:** fix what the run shows, one finding at a time, with the owner's call on each:
   - say in the tagging prompt when to tag an "anyone would" moment, and when to write one unclear Observation instead of one clear or two;
   - consider narrowing CONF.AVOID.BELONG's `anyone_would_when` power `above` to people outside family (a new catalog version);
   - the CTRL "real crisis" direction.
5. **Agent:** build the tagging prompt's tag lists (relationship, power, setting, stance) from the enums in `core/models.py`, so prompt and code can't drift apart (20 → 11).
6. **Agent:** add a test that every Move and Need field survives the copy into the Eval database, so Evals run on what the live app runs on (20 → 02, `adapters/evals/environment.py`).
7. Re-run and record the score.

Any prompt reload must keep Admin edits: use issue 28's helper.

## Acceptance criteria

- [ ] The owner corrected the drafted Tagging cases, and the box in issue 20, section 14 is ticked
- [ ] All 68 cases have run once against the 15-type catalog, and expectations that fit a new look-alike are corrected
- [ ] Cases exist for exclusions, ruled-out topics (raised by Zeph and by the User) and Prediction outcomes
- [ ] Each failing group from run `4352910b` is fixed or has the owner's decision to leave it, recorded in Comments
- [ ] The tagging prompt's tag lists are built from the enums, with a test
- [ ] A test fails if a Move or Need field is left out of the Eval database copy
- [ ] The final run's score, Eval Run ID and cost are in Comments
- [ ] The owner was shown the estimate before each run
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass, and the change was checked in the running app (`/run`)

## Let go (owner, 25 Nov 2026)

- An unclear case passing with the wrong look-alike pair (`matches` in `core/evals/tagging_eval.py`).
- The rough cost estimate for never-run cases; it corrects itself after one run.

## Comments
