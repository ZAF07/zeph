# 02 — Backend tests take about 12 minutes because they run one at a time

Status: needs-triage

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
