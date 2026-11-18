# 05 — Check-in model calls run side by side

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** See `.scratch/check-in-job/PRD.md` for the findings and options. Open questions for the grill: how many at once (config or Admin setting), and model and Telegram rate limits when many Users are due at once, e.g. when Quiet Hours end.

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

Due Users who go to the Check-in model are decided a few at a time, side by side, instead of one after another, with a fixed, small limit on how many at once. Each User's decision reads the current time when it starts, so `decided_at` and the local time told to the model are right even late in a batch. The Due Time save check stays the guard against a Check-in going out twice, including when a reply weaves it in at the same time.

## Acceptance criteria

- [ ] A batch of due Users finishes in about (Users ÷ limit) model calls' time, not Users × one call.
- [ ] No more than the limit run at once.
- [ ] Each Check-in's `decided_at` and the local time given to the model are when that User was decided.
- [ ] One User's failure doesn't stop the others.
- [ ] Tests cover the limit, per-User times and a failure in the middle.
- [ ] A `/run` with many due Users (shift Due Times back in the database) shows the batch time drop in issue 01's logs.

## Blocked by

- `.scratch/check-in-job/issues/01-tick-timing-and-backlog-logged.md`
- `.scratch/check-in-job/issues/03-check-ins-run-in-their-own-loop.md`
- `.scratch/check-in-job/issues/04-bulk-load-check-in-model-facts.md`

## Comments
