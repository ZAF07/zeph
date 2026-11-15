# 24 — "Delete my account" sometimes starts data deletion

Status: ready-for-agent

## What

Found while doing issue 18 (2026-11-15). Settings eval `delete-account` ("delete my account please", must call no tool) called `start_deleting_my_data` in 1 of 7 runs on `main` at `d610378`.

Zeph can't delete accounts (that's on the Dashboard), so the model sometimes reaches for the closest tool instead. Issue 18's "Get it done" Need ("Do it now with the right tool… don't ask them to confirm first") makes this more likely. Its "never do something else in its place" wording reduced it but didn't stop it. Before that Need was added, delete-account didn't fail this way.

Harm is low: the tool only starts Delete My Data. Nothing is deleted unless the User replies with the confirmation word on its own, and any other reply cancels it. The User still gets a confusing reply that offers the wrong thing.

## Repro

```sh
set -a && . ./.env && set +a
for i in 1 2 3 4 5; do uv run pytest -n 0 evals -m eval -k delete-account -q; done
```

Expect about 1 failure in 7 runs (`FAIL delete-account … called start_deleting_my_data`).

## Fix

Tighten the `start_deleting_my_data` tool description in `src/companion/core/chat_settings.py` (fixed text in code, not an Admin setting, so no migration is needed). Today it reads: "Start deleting the person's data when they clearly ask to delete their data. Nothing is deleted until they reply with the confirmation word." Add that it never applies to deleting their account: for that, Zeph tells them it's on the Dashboard (Account and privacy) and calls no tool.

## Acceptance criteria

- [ ] The tool description says it is only for deleting their data, never their account, and that account deletion is on the Dashboard
- [ ] Settings `delete-account` passes 5 runs in a row
- [ ] Settings `delete-my-data` still passes 5 runs in a row
- [ ] `make check-python` passes

## Comments

- 2026-11-15 (filed): eval counts from issue 18's runs: delete-account 6 of 7, delete-my-data 7 of 7. If the wording alone doesn't get to 5 in a row, the next step is a code guard (the Understanding flags "asks to delete their account" and the reply isn't offered the tool), which would need a grilling first.
