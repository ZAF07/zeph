# 22 — Tagging context lines gender the User

Status: ready-for-agent
Track: B

## Symptom

The Pattern tagging step writes each Observation's context line with a guessed gender for the User: "After agreeing to her mother's Christmas invitation on the phone, she spent the evening resentful…", "Explaining why she gave in to her mother's Christmas plan…", "She settled the Christmas conflict…". Expected: the User is never given a gender; context lines use "they/them" (or name no one).

Impact: context lines are shown to Users as "Zeph's note" on Memories → "Things you said that Zeph kept" (issue 13), so a User can be misgendered on their own page. No crash.

## Repro

Tagging Eval run `4352910b` (24 Nov 2026, live settings, real model), case `conf-mum-holiday-plans`: all three kept Observations' context lines say "she". The case's text never gives the User's gender. Not deterministic (model output), but seen in the first full run.

## Suspected location

The tagging prompt, `pattern_tagging_prompt` in `src/companion/seed/platform_settings.yaml`: it doesn't say how to refer to the User. Found while building issue 14; logged in issue 20 ("Tagging context lines call the User 'she'").

## Acceptance criteria

- [ ] The tagging prompt tells the step never to guess the User's gender and to write "they/them"; a migration reloads the stored prompt from the seed on existing databases, as 0038 and 0081 did (Pattern noticing is off for everyone, so no live edit is expected)
- [ ] A Tagging Eval check fails a case whose kept context line uses he, she, him, her, his, hers, himself or herself (for anyone: code can't tell who a pronoun means, so others are named by name or role)
- [ ] The bug no longer reproduces: `conf-mum-holiday-plans` and other cases run with the real model write no gendered context line
- [ ] A test covers the fixed behaviour
- [ ] Checks pass: `make check` (ruff, ruff format, mypy, pytest; pnpm lint, format:check, typecheck, test)
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked

## Comments

Plan (24 Nov 2026, branch `pattern-22-context-pronouns`): the `context` line rule in `pattern_tagging_prompt` says never to write he/she/him/her/his/hers about anyone (the User is "they"; others by name or role, e.g. "their mother"); migration 0088 deletes the stored prompt so it reloads from the seed; the Tagging Eval gains a code check on every kept context line (`no he or she`), which fails the case. Not in code on the live path: dropping or rewriting an Observation for its wording would lose evidence, so the prompt plus the Eval check are the fix.
