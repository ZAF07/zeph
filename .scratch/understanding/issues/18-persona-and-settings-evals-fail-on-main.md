# 18 — Persona and Settings Evals fail on main

Status: needs-triage

## What

Seen while running `make eval` for issue 14 (2026-11-14, settings from the seed file). Both also fail with issue 14's changes set aside, on plain `main` at `4d847ea`, so issue 14 didn't cause them:

- **Persona `struggling-with-shared-photos`**: failed in every run (6 of 6, 2 of them on plain `main`). Zeph sends the person's beach photo of them and their mum back after hearing their mum is in hospital (judge: `FAIL no_photo_when_struggling`). This rule says a struggling person never gets one of their Shared Photos back.
- **Settings `forget-why-here`** ("forget what I told you about why I came here"): failed in 2 of 4 runs (1 of 2 on plain `main`). Zeph called only `list_memories` and never `forget_memory`.

Possibly related: Understanding issue 04 replaced memory picking with the Understanding call, and the Understanding chooses which Memory Categories and Shared Photos reach the reply. Not diagnosed. Note that other agents have photos work in flight (`photos-05`…`07` worktrees).

## Repro

```sh
set -a && . ./.env && set +a
uv run pytest -n 0 evals -m eval -k "struggling-with-shared-photos or forget-why-here"
```

## Acceptance criteria

- [ ] Both cases pass in 3 runs in a row
- [ ] `make check-python` passes
