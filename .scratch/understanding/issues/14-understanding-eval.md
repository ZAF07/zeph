# 14 — Understanding Eval

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

A new Eval (`make eval`, never in normal checks) through the real reply path and the platform settings Admins have set, with its cases in data files (not Python), so they can move to the future Eval dashboard (`.scratch/eval-dashboard/`). Each case is a made-up User Memory and history plus a Message, with a check; the Judge marks reply-quality checks and gives a reason. It reports time and tokens for the Understanding call. Eval runs keep full content in the Model Call Log.

Cases:
- Need picked: a rant, a request for advice, small talk, a Goal slip
- A rant gets no fixing (Judge)
- Being reminded: "my sister's wedding is next week" with a 9-month-old open Thread → found and raised naturally (Judge)
- Leave it alone: same Thread while the User struggles with something else → found, not raised
- No repeat: a Thread raised earlier in the Conversation → not raised again
- Brushed off before → not raised too soon
- Strong mood, unknown cause → gentle probe (Judge)
- Curiosity due ("presentation Thursday", now Friday) → raised, at most once per Conversation
- Knowledge: used for a reflective question, not for a vent

## Acceptance criteria

- [ ] Cases live in data files and are loaded by the Eval
- [ ] Every case runs through the real reply path with real models
- [ ] Report shows pass/fail per case, the Judge's reasons, and Understanding time and tokens
- [ ] Existing Persona, Knowledge, Safeguard and Settings Evals still pass
- [ ] Eval runs record full content in the Model Call Log
- [ ] `ruff`, `ruff format --check`, `mypy` pass; `make eval` run once with results reported in Comments

## Blocked by

- `.scratch/understanding/issues/07-knowledge-when-it-helps-and-scoped-search.md`
- `.scratch/understanding/issues/10-user-portrait.md`
- `.scratch/understanding/issues/11-curiosities.md`

## Comments

### 2026-11-14 — built, `make eval` run

What was built (branch `understanding-14-understanding-eval`):

- `evals/cases/understanding.yaml`: 12 cases, 13 Messages, as plain data (made-up memory, earlier messages, Messages with what to expect, Judge rules). Loaded by `load_understanding_cases` in `evals/cases.py`, which refuses unknown rules or Thread titles, duplicate IDs, and a Thread "raised in this Conversation" with no earlier messages.
- `evals/made_up_memory.py`: saves the made-up Portrait, Memory Items, Summaries (embedded), Life Threads (embedded and name-keyed as the keeper does) and Curiosities through the real repositories, and opens a Conversation with the earlier messages. Knowledge documents are uploaded through the admin API and get the case's "when it helps".
- `evals/test_understanding_eval.py`: sends each Message through the real webhook and reply path with real DeepSeek and fastembed. It reads the saved Understanding and the Model Call Log (`evals/understanding_checks.py` holds the checks: need, found, raised, not raised, curiosity, asked why, knowledge). It also checks every model call kept full content, and has the Judge mark the case's rules.
- `evals/running_clock.py`: a clock that moves with real time but doesn't wait on typing pauses, so the Model Call Log records real Understanding times. Used by this eval only (see issue 16 for why it isn't used everywhere yet).
- Report section in `evals/report.py`: pass/fail per Message and check, the Judge's reasons, each Understanding call's time and tokens, and average/slowest time and average tokens.
- Tests: `tests/test_understanding_eval_helpers.py` (loader, checks, report).

`make eval` (2026-11-14, settings from the seed file, worktree app database not running), second full run:

```
Safeguard: 32 of 32 right
Persona: 22 of 23 rules kept
    FAIL no_photo_when_struggling (struggling-with-shared-photos)
Knowledge: 8 of 8 steps right
Settings: 13 of 14 right
  FAIL forget-why-here: expected forget_memory, called no tool
Photo descriptions: 1 of 1 right
Understanding: 9 of 13 messages passed (28 of 32 checks, 8 of 9 rules)
  Understanding calls: 13, 1463 ms on average (slowest 1877 ms), 1494 tokens in and 128 out on average
      FAIL need: picked Think it through, expected Advice        (advice-is-asked-for)
      FAIL need: picked Be heard, expected Accountability        (goal-slip)
      FAIL raised: didn't bring up Falling-out with Mei          (reminded-of-sister; found: PASS)
      FAIL raises_sister_naturally                               (reminded-of-sister)
      FAIL asked why: didn't ask why                             (strong-mood-unknown-cause; gentle_probe judge: PASS)
Tokens used (app and judge): 343218 in, 15529 out; 6 min 21 s
```

All passing: rant gets no fixing (Judge), small talk, sister left alone while struggling, no repeat in the Conversation, brushed-off Thread not raised too soon, Curiosity raised once then not again, Knowledge chosen for a reflective question and not for a vent, full content kept for every model call.

Notes:

- The 4 Understanding failures are real model behaviour, not harness errors: a failed case prints what the Understanding was given and what it answered, and the input was right (e.g. the Mei Thread was shown, but the model picked "Just chatting" and brought nothing up). Tuning the Understanding prompt and Needs is follow-up `17-tune-understanding-with-the-eval.md`.
- Persona `struggling-with-shared-photos` and Settings `forget-why-here` also fail on plain `main` (checked by setting this branch's changes aside: Persona failed 2 of 2, Settings 1 of 2). They are not caused by this change and were left alone.
- First run with the real-time clock in every eval broke the Knowledge eval 3 of 3 times (vs 3 of 3 passes with the frozen clock). Cause: a real defect in shipped code, filed as `16-knowledge-dropped-when-document-named-by-its-whole-line.md`.

### 2026-11-14 — `/code-review` fixes, Understanding eval rerun

Review (Standards: no hard violations; Spec: two partial, four shaky). Fixed:

- Knowledge check now also needs passages to reach the reply (read from the reply call's instructions in the Model Call Log), not only that the Understanding chose a document.
- The loader refuses a Life Thread title written anywhere else in the case (Portrait, items, Summaries, Curiosities, Knowledge, earlier messages, Messages), so "found" only passes when the Companion was reminded.
- A Message logging more than one Understanding call uses the last one instead of crashing.
- The long eval test is split (`send_and_collect_lines`, `check_message`, `latest_understanding`, `calls_in_new_traces`). Keyword arguments for `list_traces`. One helper replaces three repeated Thread-check loops. Reactions and sensitivity are kept as enums. The day and minute offsets in `made_up_memory.py` are named.
- The existing Persona and Settings failures are filed as `18-persona-and-settings-evals-fail-on-main.md`.

Left as is: importing `wait_until_ready` from the Knowledge eval (the repo already does this between test modules). For "no repeat" and "brushed off", the "not raised" check is mostly guaranteed by the hold-back code, so the Judge rules are what test the reply there. For the Curiosity case, the second Message passes because the raised Curiosity is no longer due, not because of the per-Conversation limit.

Understanding eval rerun after the fixes (`-k understanding`):

```
Understanding: 9 of 13 messages passed (28 of 32 checks, 9 of 9 rules)
  Understanding calls: 13, 1352 ms on average (slowest 1674 ms), 1492 tokens in and 126 out on average
      FAIL need: picked Think it through, expected Advice
      FAIL need: picked Be heard, expected Accountability
      FAIL asked why: didn't ask why
      FAIL knowledge: chose “The Second Arrow” (Owner's notes, Buddhism), but no passage reached the reply   ← bug 16
Tokens used (app and judge): 58389 in, 2700 out
```

`reminded-of-sister` passed this run (it failed in the two before), so results vary from run to run.
