# 38 — Three Predictions per Pattern Type, followed up when the User next talks about it

Status: ready-for-agent
Track: shared
Blocked by: 36 (same confirm rule)

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answer 8 and the owner's added item on follow-ups.

## What to build

1. **Three Prediction wordings per Pattern Type (answer 8).** The catalog field becomes a list, `prediction_wordings`, each testing a different side of the Pattern. Claude drafts three for each of the 15 Pattern Types (new catalog versions); the owner corrects them later (added to the owner's list in issue 20).
2. **Code picks one not used yet.** A Prediction keeps which wording it came from (`predictions.wording_number`). Sharing gives the first; a new Prediction is the first wording this Pattern hasn't had, and when all were given, the one given longest ago.
3. **Two that came true are two different tests.** Confirming by Predictions counts each wording once.
4. **Follow up when they next talk about it.** A follow-up Curiosity may be asked before its first day when a Life Thread the Pattern showed in comes to mind in a reply on a later day than the Prediction was given. The Admin-set wait (7 days) stays as the fallback, and the last day stays.
5. **A guide for the owner:** `docs/pattern-catalog/README.md` gains a section on writing and correcting Prediction wordings.

## Acceptance criteria

- [ ] Every Pattern Type has three Prediction wordings, and the catalog refuses fewer than one
- [ ] A new Prediction uses a wording the Pattern hasn't had, with a test
- [ ] The same wording coming true twice doesn't confirm; two different ones do, with tests
- [ ] A follow-up is offered early when a Life Thread of the Pattern is in mind on a later day, and not on the day the Prediction was given, with tests
- [ ] The Admin Pattern Catalog page shows all the wordings
- [ ] The guide is written, and the owner's correction step is on issue 20's list
- [ ] `ruff`, `ruff format`, `mypy`, `pytest` and the web checks pass, and it was checked in the running app

## Comments
