# 06 — Cancel pressed after the last case, and SGD in the `make eval` report

Status: in-progress

## Parent

`.scratch/eval-dashboard/issues/archive/03-cost-traces-re-runs-and-history.md` (two known limits left there)

## What to build

- **Cancel after the last case:** if an Admin presses Cancel after the runner's last stop check but before it ends the run, the run ends Finished with the cancel flag set, so the page goes from "Cancelling…" to "Finished". A run an Admin asked to cancel should end Cancelled, decided in the same step that ends it.
- **SGD in the terminal report:** `make eval` prints tokens but not cost. Add the run's SGD (at the prices it started with) and any models with no price set, as the Dashboard shows.

## Acceptance criteria

- [ ] A run whose cancel was asked for ends Cancelled even when every case had finished (test)
- [ ] The `make eval` report prints the run's SGD and names models with no price set (test)
- [ ] Verified at `/run`; `make check-python` and `make check-web` pass

## Blocked by

None

## Comments
