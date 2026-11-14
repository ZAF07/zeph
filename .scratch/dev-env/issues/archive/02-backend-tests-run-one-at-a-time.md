# 02 — Backend tests take about 12 minutes because they run one at a time

Status: in-progress

## Symptom

The full backend suite (`uv run pytest`) takes about 12 minutes: 834 passed, 9 deselected in 739.59s on 14 Nov 2026, in the issue 09 worktree. Expected: a few minutes, so every issue's full-suite gate doesn't hold up the work.

Nothing crashes. It is slow, and slower still when several agents run their suites at once (load average about 7 during that run).

Likely causes (not measured yet):

- Most tests go through the whole app against a real Postgres, e.g. sign up, link Telegram, have a Conversation and its end, then check through the API.
- pytest runs the tests one at a time; `pytest-xdist` isn't installed.

## Repro

```bash
time uv run pytest -q
```

Deterministic: always about this slow on a busy machine.

## Idea (not decided)

Run tests in parallel with `pytest-xdist` (`pytest -n auto`). Each worker needs its own database. `tests/conftest.py` `database_url` is session-scoped and starts its own throwaway Postgres container (testcontainers), and under xdist each worker is its own session, so each worker may already get its own container. Check that before building anything. Also check the cost of N containers starting at once, and any tests that share state outside the database (files, ports, module-level state).

Run `uv run pytest --durations=20` first to see whether a few slow tests are most of the time.

## Acceptance criteria

- [ ] The full backend suite runs much faster (say under 4 minutes on a normal machine), with the time before and after recorded here
- [ ] Every test still passes, run in parallel and run on its own
- [ ] `make check` (or whatever runs the full suite) uses the faster way
- [ ] Quality gates pass: `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy src`

## Comments

Diagnosis, 14 Nov 2026 (worktree `ai-chat-companion-dev-env-02`, 10 cores):

- **Baseline, one at a time:** 834 passed in 288s (4m48s), load about 7. The 12 minutes in the symptom was mostly other agents' runs competing for the machine.
- **No slow outliers.** `--durations=40`: the slowest is the 7s Postgres start, then nothing over 1.2s. Time is spread across 834 tests at about 0.35s each, with only 38% CPU used (waiting on the database). Per-test setup on a quiet machine is about 0.3s: TRUNCATE 0.13s, building the app 0.1s, seeding 0.04s.
- **Plain `-n auto` broke:** 349 passed, 485 errors in 53s. Each of the 10 workers started its own Postgres plus a Ryuk cleanup container at once; some Ryuk containers were not ready in time (`ConnectionError: Port mapping for container ... and port 8080 is not available`), and the Postgres containers of those workers were left running.
- **Confirmed cause and fix:** tests ran one at a time; running them in parallel needs one shared Postgres, not one per worker. `tests/conftest.py` now starts one Postgres in the main pytest process (`pytest_configure`) and hands its URL to each xdist worker (`pytest_configure_node`); each worker makes its own database `companion_test_<worker id>` and migrates it. Migration tests downgrade only their own worker's database.
- The main process starts that Postgres only the first time it is asked for (when the first worker starts, or when a test first needs the database). A run with no database tests starts no container; a parallel run starts one (checked with `docker events`: 0, 1 and 1 containers made).
- **State outside the database:** checked. File writes use `tmp_path`, nothing binds ports, no `setenv`, no module-level state changed by tests.
- `pytest-xdist` added to dev dependencies; `-n auto` is in pytest's `addopts`, so plain `uv run pytest` and `make check` run in parallel. `make contract` and `make eval` pass `-n 0`: they call real services, and the eval report is kept in one pytest process, so under workers it would print empty.
- **After, in parallel:** 836 passed in 72.5s, 92.5s and 77.9s on three runs (load 6 to 10). No test containers left afterwards.
- **One at a time (`-n 0`):** 836 passed in 573s (load 10 to 12).
- A small run pays about 3s for starting workers (2 files: 3.1s with `-n 0`, 6.0s with `-n auto`). Use `-n 0` for quick single-file runs.
