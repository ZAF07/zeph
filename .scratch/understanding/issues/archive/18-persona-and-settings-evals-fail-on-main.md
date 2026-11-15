# 18 — Persona and Settings Evals fail on main

Status: completed

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

- [x] A struggling User who didn't ask is never offered `send_photo` (unit test on the guard): `tests/test_may_send_photo.py`, and through the reply path `test_a_struggling_user_who_did_not_ask_is_not_offered_their_photo` (red before the guard, green after)
- [x] A struggling User who asks for a photo is offered `send_photo` (unit test): `test_a_struggling_user_who_asks_for_their_photo_is_offered_it`
- [x] Persona eval: a struggling User who asks for a photo can get one back (new case): `struggling-asks-for-photo`, rule `photo_sent_when_asked`; passed 5 of 6 runs, the last 4 in a row
- [x] `forget-why-here` seeds two Memory Items; passes only when the right one is deleted and the other stays: `memories` / `forgotten` in `evals/cases/settings.yaml`, checked by `SettingsResult`
- [x] Both cases pass in 3 runs in a row (after issue 21): `struggling-with-shared-photos` 4 of 4; `forget-why-here` 4 of 4 after the onboarding fix (see Comments)
- [x] `make check-python` passes: ruff, ruff format, mypy clean; 957 passed
- [x] (added from the comment below) Settings `delete-my-data` fixed with a "Get it done" Need: 7 of 7 eval runs called `start_deleting_my_data`

## Blocked by

- `.scratch/understanding/issues/archive/21-reasoning-calls-default-to-reasoner.md` (completed 2026-11-15)

## Comments

- 2026-11-15 (implemented; evidence):
  - **Guard:** `UnderstandingForm.struggling` and `asked_for_photo` (anything but `true` reads as false; forms saved before read as false). `may_send_photo(form)` in `core/understanding.py`; `ReplyService` passes no Shared Photo IDs to the reply when it says no, so `send_photo` isn't offered, while the photo descriptions still reach the reply in the memory text. Understanding prompt asks for both; migration 0039 reloads it.
  - **"Get it done" Need**, before Ask more, with the wording fix: "Do only what they asked: if Zeph can't do it, say where they can, and never do something else in its place." Seed file plus migration 0040, which adds it to an existing install just before the fallback unless a Need already has the name (ignoring case). Checked on the worktree DB: rolled back to 0038 with main's old prompt, upgraded, got the new prompt and the Need in order.
  - **`forget-why-here`:** the first 3 runs failed: `forget_memory` was called but deleted an onboarding Goals item ("Came to Zeph for: …" / "what brings them here"), which is also why they came. Fixed by having a case with its own `memories` onboard without "What brings you here?", so only the case's items say why they came. 4 of 4 after (3 targeted runs + the full eval).
  - **Evals** (deepseek-reasoner defaults from issue 21): targeted runs (Persona struggling cases + all Settings) 3×, then 3× of the cases still open, then one full `make eval`: **70 of 70 passed, 0 failures** (Safeguard 32/32, Persona 25/25 rules, Knowledge 8/8, Settings 14/14, Photo descriptions 1/1, Understanding 13/13 messages, 32/32 checks) vs 4, 5, 4 failures per run before. Across all runs: delete-my-data 7/7, quiet-after-nine 7/7, memory-off 7/7, struggling-with-shared-photos 4/4, struggling-asks-for-photo 5/6 (one fail in the first round; the output filter hid which rule), **delete-account 6/7** (one run started data deletion: the risk this comment noted; not in the criteria, still open).
  - **/run** (real app on the worktree's Postgres at 0040, real DeepSeek and fastembed; chat channel, clock, scheduler, timer and auth faked as a worktree has no Telegram chat): struggling without asking → `struggling: true`, `send_photo` not offered, no photo; asking for the Penang photo → `struggling: true`, `asked_for_photo: true`, Need "Get it done", `send_photo` called, photo sent; "please delete all my data" → `start_deleting_my_data`; "delete my account please" → no tool, points to the Dashboard; "forget what I told you about why I came here" → `list_memories` then `forget_memory`, the work-stress item gone, the Sunday-walk item kept.
  - **Seen, not fixed (Safeguard):** in the /run, "she's back in hospital. they said it's her heart this time" got the Crisis Reply (helplines), and one eval run's judge mentioned a helpline in the asks-for-photo case. A Safeguard false alarm on a parent's illness; worth its own bug if it recurs.
  - Review: Standards and Spec reviews found no hard issues in `src/`; fixed: a direct unit test on the guard, one shared `SettingsCase.memory_item_contents`, clearer test names, CONTEXT.md (Understanding and Need entries). Kept: test-helper one-line docstrings (match sibling tests); `may_send_photo` as a free function (matches the module).

- 2026-11-15 (grilling, done): decisions above. Ready for `/implement`; final 3-run check waits on issue 21.
- 2026-11-15 (grilling, paused): rerun both cases on reasoner once issue 21 is done. Open question: a code guard where the Understanding says the User is struggling and the reply then isn't offered `send_photo` (recommended; the rule today is only tool-description wording). `forget-why-here` not discussed yet.
- 2026-11-15 (found while doing issue 21; **open question for this issue**: Settings `delete-my-data` now drops on reasoner and isn't in the criteria above; the user chose to fix it here. `forget-why-here` stays the eval bug decided above): **no Need fits "do something for me"** (change a setting, forget something, delete my data), so the Understanding picks the fallback **Ask more**, whose how-to-reply says "Don't guess… ask one simple question… before going deeper". The reply then asks or offers instead of calling the tool. Seen with a probe that sends one message to a fresh User in the real app (worktree DB, real DeepSeek) and reads the Model Call Log:
  - "please delete all my data", 8 runs each: Understanding picked Ask more 15 of 16 times, nuance like "clarify what they want deleted and confirm before anything irreversible". Reply called `start_deleting_my_data` 5/8 on deepseek-chat, **1/8 on deepseek-reasoner** (reasoner follows the "confirm first" advice more faithfully). Over 8 eval runs each: delete-my-data 6/8 chat, 4/8 reasoner; forget-why-here 3/8 chat, 4/8 reasoner; quiet-after-nine 5/8 chat, 6/8 reasoner.
  - **Trial fix** (worktree only, then removed): a Need placed before Ask more:
    ```yaml
    - name: Get it done
      when_it_fits: >-
        They ask Zeph to do something it can do for them: change a setting, turn
        something on or off, forget something, or delete their data.
      how_to_reply: >-
        Do it now with the right tool, then say plainly what you did. Don't ask
        them to confirm or explain first: a tool that needs confirming asks for it
        itself. Ask only if you truly can't tell what they want changed.
    ```
    Probe on reasoner, 6 runs each: delete-my-data 5/6, forget-why-here 6/6 (`list_memories` then `forget_memory`), quiet-after-nine 6/6. Full `make eval` 3×: Settings 12/14, 14/14, 14/14; total failures 6, 2, 1 (vs 4, 5, 4 on reasoner without it).
  - **Needs a wording fix before use:** with it, "delete my account please" (must call no tool) called `start_deleting_my_data` in 1 of 3 eval runs and 1 of 5 probes: the reply said it can't delete accounts, then offered and started data deletion. Something like "Only do what they asked; if Zeph can't do it, say where they can, and don't do something else in its place." Re-measure delete-account, memory-off and advice-is-asked-for (each failed once in the 3 runs) after.
  - Not caused by the trial Need: Persona `asks-for-tips` failed `no_lists` in 2 of 3 runs with it, but the Understanding picked Advice in 5 of 5 probes; the Advice reply sometimes writes tips as separate lines.
  - A new Need is an Admin-managed row (ADR-0004): the seed file only loads when there are no Needs, so the local main DB needs it added by hand.

## Completion

- Completed: 2026-11-15
- Commits: `0389b4e` (photo guard, Understanding prompt and migration 0039, Get it done Need and migration 0040, eval cases), `5579b85` (review fixes, guard unit test, CONTEXT.md), `b511515` (forget-why-here User skips onboarding reasons), `86925e5` (archive with evidence); merged to main in `cd5a050`
