# 14 — Understanding Eval

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

A new Eval (`make eval`, never in normal checks) through the real reply path and the platform settings Admins have set, with its cases in data files (not Python), so they can move to the future Eval dashboard (`.scratch/eval-dashboard/`). Each case is a made-up User Memory and history plus a Message, with a check; the Judge marks reply-quality checks and gives a reason. It reports time and tokens for the Understanding call. Eval runs keep full content in the Model Call Log.

Cases:
- Need picked: a rant, a request for advice, small talk, a Goal slip
- A rant gets no fixing (Judge)
- Being reminded: "my sister's wedding is next week" with a 9-month-old open Thread → found and raised naturally (Judge)
- Leave it alone: same Thread while the User struggles with something else → found, not raised
- No repeat: a Thread raised earlier in the Conversation → not raised again
- Brushed off before → not raised too soon
- Strong mood, unknown cause → gentle probe (Judge)
- Curiosity due ("presentation Thursday", now Friday) → raised, at most once per Conversation
- Knowledge: used for a reflective question, not for a vent

## Acceptance criteria

- [ ] Cases live in data files and are loaded by the Eval
- [ ] Every case runs through the real reply path with real models
- [ ] Report shows pass/fail per case, the Judge's reasons, and Understanding time and tokens
- [ ] Existing Persona, Knowledge, Safeguard and Settings Evals still pass
- [ ] Eval runs record full content in the Model Call Log
- [ ] `ruff`, `ruff format --check`, `mypy` pass; `make eval` run once with results reported in Comments

## Blocked by

- `.scratch/understanding/issues/07-knowledge-when-it-helps-and-scoped-search.md`
- `.scratch/understanding/issues/10-user-portrait.md`
- `.scratch/understanding/issues/11-curiosities.md`
