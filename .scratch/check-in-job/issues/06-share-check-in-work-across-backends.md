# 06 — Check-in work is shared across backends

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** This is a hard-to-reverse choice and needs an ADR (it touches ADR-0003 ports and adapters and ADR-0005 Docker Compose). Grill it together with `.scratch/scaling/issues/01-run-more-than-one-backend.md`. See `.scratch/check-in-job/PRD.md` for options B (claim in the database) and C (job queue).

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

More than one backend or worker can decide on Check-ins at the same time without two of them taking the same User. The leading option is for each worker to claim a batch of due Users in Postgres (`FOR UPDATE SKIP LOCKED` with a short claim lease, so a crashed worker's Users become due again). The `Scheduler` port stays the same. The Check-in loop may run in its own worker container. A job queue (option C) is the fallback if the grill finds more background work coming.

## Acceptance criteria

- [ ] With two workers running, each due User is sent to the Check-in model once, not twice.
- [ ] A worker that dies mid-batch leaves its claimed Users due again after the lease ends.
- [ ] An ADR records the choice.
- [ ] Tests cover two workers claiming at once and an expired lease.
- [ ] A `/run` with two workers against the same database shows the work split between them and no double model calls.

## Blocked by

- `.scratch/check-in-job/issues/05-check-in-model-calls-side-by-side.md`
- The grill of `.scratch/scaling/issues/01-run-more-than-one-backend.md`

## Comments
