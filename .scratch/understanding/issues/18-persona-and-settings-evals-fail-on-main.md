# 18 — Persona and Settings Evals fail on main

Status: ready-for-agent

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

## Decisions (grilling, 2026-11-15)

- **Rule:** never send a Shared Photo back when the User is struggling, unless they ask for one. The reply still sees the photo descriptions, so it may mention the memory in words. Why: a photo can sting (beach photo with mum while mum is in hospital), can read as "cheer up" instead of listening, and the model can't reliably tell an encouraging photo from a painful one.
- **Code guard:** add `struggling: bool` and `asked_for_photo: bool` to `UnderstandingForm`. The reply is offered `send_photo` only when `not struggling or asked_for_photo`. Update the seeded Understanding prompt to fill both (needs a migration that reloads it, like 0037).
- **`forget-why-here` is an eval bug:** the eval User has no memories, so `list_memories` returns nothing and not calling `forget_memory` is correct. Fix the case: give that User two Memory Items, one about why they came (e.g. "came here because work stress is wearing them down") and one unrelated. Pass only if that item is deleted and the other stays.
- The guard and the eval fix don't need issue 21; only the final "3 runs in a row" check runs after it.

## Acceptance criteria

- [ ] A struggling User who didn't ask is never offered `send_photo` (unit test on the guard)
- [ ] A struggling User who asks for a photo is offered `send_photo` (unit test)
- [ ] Persona eval: a struggling User who asks for a photo can get one back (new case)
- [ ] `forget-why-here` seeds two Memory Items; passes only when the right one is deleted and the other stays
- [ ] Both cases pass in 3 runs in a row (after issue 21)
- [ ] `make check-python` passes

## Blocked by

- `.scratch/understanding/issues/21-reasoning-calls-default-to-reasoner.md`

## Comments

- 2026-11-15 (grilling, done): decisions above. Ready for `/implement`; final 3-run check waits on issue 21.
- 2026-11-15 (grilling, paused): rerun both cases on reasoner once issue 21 is done. Open question: a code guard where the Understanding says the User is struggling and the reply then isn't offered `send_photo` (recommended; the rule today is only tool-description wording). `forget-why-here` not discussed yet.
