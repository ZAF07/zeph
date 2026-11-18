# 01 — Tick timing and the Check-in backlog are logged

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** See `.scratch/check-in-job/PRD.md` for the findings and options.

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

Each scheduler tick logs how long it took overall and for each part (Conversation ending and processing, Portraits, Check-ins, retention, auth deletions), plus how many Users were due a Check-in, how many were held back, how many went to the Check-in model and how many failed. Then run a tick against a copy of the main database (`make db-copy`) and record the real numbers here. They decide whether issues 03–05 are worth doing and how big the thread pool in 05 should be.

## Acceptance criteria

- [ ] A tick logs its total time and the time of each part.
- [ ] A tick logs the due, held-back, sent-to-model and failed counts for Check-ins.
- [ ] Tests cover the counts that are logged.
- [ ] A `/run` against copied data shows the log lines, and the numbers are recorded under `## Comments`.

## Blocked by

None - can start immediately

## Comments
