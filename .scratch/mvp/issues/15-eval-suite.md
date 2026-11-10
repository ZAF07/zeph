# 15 — Eval suite and README

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

A way to measure the Companion's behaviour with the real LLM, run separately from normal checks with `make eval`. Safeguard evals use ~30 labelled messages (clear crises, subtle crises, false alarms like "this traffic is killing me"); the target is that every real crisis is caught. Persona evals run a few scripted conversations, judged by an LLM against the Persona rules (no bullet lists, no "As an AI…", not preachy, honest when asked if it's human, gentle about dependency). A README explains how to run the evals, what they cost, and how to read the results.

## Acceptance criteria

- [ ] `make eval` runs Safeguard and Persona evals against the real configured LLM, using the current prompts from settings
- [ ] `make eval` is not part of `make check`
- [ ] Safeguard evals report each missed crisis and each false alarm, and fail if any real crisis is missed
- [ ] Persona evals report a pass/fail per rule per scripted conversation, with the judge's reason
- [ ] The eval cases are data files, easy to add to
- [ ] An eval README explains: setup, how to run, rough cost, how to read results, when to run (after changing Safeguard or Persona prompts or models)
- [ ] `make check` passes
- [ ] `make eval` has been run once and its output reported

## Blocked by

- `.scratch/mvp/issues/05-safeguard.md`
