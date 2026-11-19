# 03 — Docker's disk fills up with test databases and build cache

Status: ready-for-agent

## Symptom

On 19 Nov 2026 Docker's disk hit 100% and the worktree stack's Postgres failed with "No space left on device", so the `/run` sign-in failed. Space taken by leftovers:

- 91 unnamed volumes no container used, about 18 GB. Each held one `pytest` run's test database.
- 6 stopped test-database containers from killed `pytest` runs.
- Build cache, about 15 GB, refilled within hours after being cleared.

Clearing them took Docker's disk from 85% to 23%.

## Causes

1. `tests/conftest.py` starts `pgvector/pgvector:pg16` for each `pytest` run. The image declares a volume at `/var/lib/postgresql/data`, so Docker makes an unnamed volume per run. It stays behind when the container is removed or the run is killed. Many agents run the suite many times a day.
2. Every `make restart` and `make worktree-setup` adds to the build cache. `make worktree-teardown` removes the worktree's images but never the cache.

## What to build

1. The test Postgres keeps its data in memory (tmpfs at its data folder), so no volume is made, even when a run is killed.
2. `make worktree-teardown` also clears build cache older than two days. Newer cache stays, so other agents' builds stay fast.

## Acceptance criteria

- [ ] A `pytest` run leaves no new Docker volume behind.
- [ ] A test checks that the test Postgres has no volume.
- [ ] `make worktree-teardown` clears build cache older than 48 hours and keeps newer cache.
- [ ] All Python checks pass.
- [ ] Run check: count volumes before and after a full `pytest` run (no change); run `make worktree-teardown` and see the cache prune line.

## Blocked by

None.
