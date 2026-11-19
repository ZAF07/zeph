# 03 — Docker's disk fills up with test databases and build cache

Status: completed

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

- [x] A `pytest` run leaves no new Docker volume behind.
- [x] A test checks that the test Postgres has no volume.
- [x] `make worktree-teardown` clears build cache older than 48 hours and keeps newer cache.
- [x] All Python checks pass.
- [x] Run check: count volumes before and after a full `pytest` run (no change); run `make worktree-teardown` and see the cache prune line.

## Blocked by

None.

## Comments

- 2026-11-19 — Done (branch `docker-01-no-leftover-test-volumes`).
  - `tests/conftest.py`: `throwaway_postgres()` builds the test Postgres with tmpfs at `/var/lib/postgresql/data`, capped with `"size=2g"`. A full run peaks near 650 MB (measured with `df` inside the container). testcontainers 4.15's docs say `size` takes `"2g"`, but Docker rejects that ("invalid tmpfs option"); it needs `"size=2g"`.
  - `Makefile`: `worktree-teardown` ends with `docker builder prune --all --force --filter until=48h`. `--all` is needed, or only loose cache is cleared (review). `until` counts from when cache was last used, and BuildKit keeps cache a running build is using, so other agents' recent builds stay fast.
  - Docs: CLAUDE.md step 7 and the run-dashboard skill say teardown also clears old build cache.
  - The test database now lives in memory, so the full suite runs faster: 2m44s–2m54s, down from 5m41s earlier the same day (load from other agents varies).
  - Before this fix, the leftovers were cleared by hand: 6 stopped test containers, 91 unused unnamed volumes (about 18 GB) and the build cache (about 15 GB). Docker's disk went from 85% to 23%.
  - Other worktrees keep making volumes until they rebase onto this change (seen: another agent's test Postgres still writing to disk during this run).

### Evidence per criterion

1. No volume left: full `pytest -n auto` runs with the volume list taken before and after: 8 before, 8 after, no new names (twice: before and after the size cap).
2. Test: `tests/test_test_database.py::test_the_test_postgres_makes_no_docker_volume` starts the test Postgres and checks its `Mounts` hold no volume. Red before the fix (the image's volume showed up), green after.
3. Teardown: `make worktree-teardown` printed `docker builder prune --all --force --filter until=48h` / `Total: 0B`. All cache was newer than 48 hours, so it was kept. The same command with `until=1m` removed 21.4 MB of cache, showing the filter removes older entries.
4. Python checks: `ruff check` All checks passed!, `ruff format --check` 506 files already formatted, `mypy` no issues found in 189 source files, `pytest` 1331 passed.
5. Run check: as in 1 and 3.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after merge>
