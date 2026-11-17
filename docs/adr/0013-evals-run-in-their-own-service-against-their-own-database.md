# Evals run in their own service against their own database

Admins start Eval Runs from the Dashboard, so Evals can no longer be pytest tests that start a throwaway Postgres container. Instead the backend saves a run as Queued, and a separate `eval-runner` service in Docker Compose (same image as the backend) picks runs up one at a time and runs them against a separate Eval database on the same Postgres server, wiped and re-seeded for each Variant. Results and each case's full-content model calls are written back to Eval-only tables in the app database, tied to the run and never to a User. `make eval` queues a run on the local stack the same way, so the terminal and the Dashboard run the same code.

## Considered Options

- **A background thread in the backend.** Rejected: a six-minute run would share the process that answers real Users, die on every backend restart, and break once more than one backend runs (`.scratch/scaling/issues/01-run-more-than-one-backend.md`).
- **Keep throwaway containers.** Rejected: the backend would need the Docker socket, which is close to root on the host.
- **Made-up Users in the app database, marked as Eval Users.** Rejected: they would leak into User lists, the Check-in scheduler and stats once the platform is live.

## Consequences

- Eval traces are not in the Model Call Log (its rows belong to a User); the Eval pages show them with the same trace view.
- The `eval-runner` is always wired with the fake chat channel and fake web search, and no Check-in scheduler runs on the Eval database, so an Eval can never reach a real chat or spend search credits. The fake web search finds only the made-up pages a case gives it (2026-11-17, so Research can be tested); with none it finds nothing.
- `make eval` needs the stack running (`make up`, or the worktree's own stack).
- A run stopped by a runner restart ends Interrupted and is never retried by itself, because runs cost money.
