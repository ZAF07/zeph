# 23 — Admins set how hard a model thinks

Status: needs-triage

## What

The user wants this later (2026-11-15): Admins can set a model's thinking effort on the Dashboard, not only turn thinking on or off. Most models offer effort levels today (DeepSeek: see the [Thinking Mode guide](https://api-docs.deepseek.com/guides/thinking_mode), "Thinking Mode Toggle and Effort Control").

Kept out of issue 22 on purpose: 22 adds the on/off Thinking switch per call. This builds on it the same way: the core asks for an effort, each model adapter turns it into what its API takes.

## To decide (grilling)

- The effort levels Admins pick from (e.g. low / medium / high), and what an adapter does when its model has fewer or none.
- Whether effort shows only when Thinking is on.
- Starting effort per call, measured with `make eval` (time and cost per Message, as in issue 21).

## Blocked by

- `.scratch/understanding/issues/22-use-deepseek-flash-with-thinking-toggle.md`

## Comments
