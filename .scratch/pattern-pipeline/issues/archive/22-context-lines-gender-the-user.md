# 22 — Tagging context lines gender the User

Status: completed
Track: B

## Symptom

The Pattern tagging step writes each Observation's context line with a guessed gender for the User: "After agreeing to her mother's Christmas invitation on the phone, she spent the evening resentful…", "Explaining why she gave in to her mother's Christmas plan…", "She settled the Christmas conflict…". Expected: the User is never given a gender; context lines use "they/them" (or name no one).

Impact: context lines are shown to Users as "Zeph's note" on Memories → "Things you said that Zeph kept" (issue 13), so a User can be misgendered on their own page. No crash.

## Repro

Tagging Eval run `4352910b` (24 Nov 2026, live settings, real model), case `conf-mum-holiday-plans`: all three kept Observations' context lines say "she". The case's text never gives the User's gender. Not deterministic (model output), but seen in the first full run.

## Suspected location

The tagging prompt, `pattern_tagging_prompt` in `src/companion/seed/platform_settings.yaml`: it doesn't say how to refer to the User. Found while building issue 14; logged in issue 20 ("Tagging context lines call the User 'she'").

## Acceptance criteria

- [x] The tagging prompt tells the step never to guess the User's gender and to write "they/them"; a migration reloads the stored prompt from the seed on existing databases, as 0038 and 0081 did (Pattern noticing is off for everyone, so no live edit is expected)
- [x] A Tagging Eval check fails a case whose kept context line uses he, she, him, her, his, hers, himself or herself (for anyone: code can't tell who a pronoun means, so others are named by name or role)
- [x] The bug no longer reproduces: `conf-mum-holiday-plans` and other cases run with the real model write no gendered context line
- [x] A test covers the fixed behaviour
- [x] Checks pass: `make check` (ruff, ruff format, mypy, pytest; pnpm lint, format:check, typecheck, test)
- [x] Each criterion above was checked in the running app (`/run`) before being ticked

## Comments

Plan (24 Nov 2026, branch `pattern-22-context-pronouns`): the `context` line rule in `pattern_tagging_prompt` says never to write he/she/him/her/his/hers about anyone (the User is "they"; others by name or role, e.g. "their mother"); migration 0089 (after main's 0088) deletes the stored prompt so it reloads from the seed; the Tagging Eval gains a code check on every kept context line (`no he or she`), which fails the case. Not in code on the live path: dropping or rewriting an Observation for its wording would lose evidence, so the prompt plus the Eval check are the fix.

Diagnosis: the `context` instruction in `pattern_tagging_prompt` said "in your words" and nothing about how to refer to people, so the model guessed a gender from the story. Feedback loop: the new Tagging Eval check (`no he or she`) on every kept context line, run with the real model.

Decisions: the check fails any he/she word in a context line, about anyone, because code can't tell who a pronoun means; the prompt asks for names or roles for others. Quotes are never checked (they're the User's own words). The check adds a failed check only (a clean line adds none), like the "Kept but not expected" checks. The migration reloads the prompt from the seed, as 0038 and 0081 did, numbered 0089 after main's 0088.

Evidence (24 Nov 2026, worktree stack on 3040/8040, real model, owner approved the full run):

- **Prompt and migration.** Fresh stack at 0089 with the new rule in the stored prompt. On the running stack, the stored prompt set to an old text and the version set back: migration 0089 deleted it and a backend restart reloaded the new one ("himself or herself" present). Test: `test_an_existing_install_reloads_the_tagging_prompt_that_never_says_he_or_she`.
- **Eval check.** Run `f7b14098` (all 44, S$0.16, 32 passed): 50 kept context lines; none gendered the User; one failed the check, "…avoid upsetting her" about the friend Priya (case `conf-rehearses-text-to-friend`), shown as `Context lines / no he or she`. Tests: `test_a_tagging_case_fails_when_a_kept_context_line_says_he_or_she`, `test_gendered_words_finds_each_he_or_she_word_once_as_a_whole_word` (6 cases).
- **No longer reproduces.** After review (prompt also names himself/herself, rebased on main's changed prompt): `conf-mum-holiday-plans` wrote "They agreed to Christmas at their mother's…", "Explaining why they gave in…", "…they brush aside their own preference…"; `conf-rehearses-text-to-friend` named Priya instead of "her" and passed. The mum case still fails on "anyone would" (issue 20), not on he/she. Other failures in the full run are the kinds already in issue 20.
- **Checks** on the final build: `make check` ruff, ruff format, mypy clean (247 files), pytest 2035 passed; `pnpm lint`, `format:check`, `typecheck` clean, `pnpm test` 137 files, 953 tests passed.
- **Review.** Standards and spec reviews run. Fixed: migration renumbered to 0089 after main's 0088, the prompt names himself/herself like the check, a clearer group-label name. Left: the word list lives in the regex and the prompt (a test ties them), migration tests copy their setup steps (already the case).

## Completion

- Completed: 2026-11-24
- Commit: c2c69c4 (merge "Merge pattern-22-context-pronouns: tagging context lines never say he or she"; work in 515dc6e "Tagging context lines never say he or she", 173a2d7 "Issue 22: review fixes (migration 0089, himself/herself), evidence, archived")
