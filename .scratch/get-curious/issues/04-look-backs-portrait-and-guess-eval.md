# 04 — Look-backs, a Portrait without open questions, and the guess Eval case

Status: ready-for-agent

## Parent

`.scratch/get-curious/PRD.md`

## What to build

- **Look-backs.** The Curiosity-keeping prompt adds roughly: "Something they vented about where Zeph only listened: a gentle look-back once it has had time to settle, asking how they see it now (e.g. 'how are you feeling about the thing with your boss now?'), with not_before at least the next day and sensitivity at least medium." So a vent comes back in a later Conversation or the Curiosity Check-in, never in the same few hours. A brushed-off look-back is handled by the existing Curiosity reactions. A Reflect Move is out of scope; it'll be grilled separately.
- **Portrait.** The Portrait prompt drops "Open questions Zeph is still curious about" and says to write only what Zeph is fairly sure of. What it only suspects lives in Curiosity guesses (issue 02, ADR-0017).
- **Running platform.** A migration reloads the Curiosity-keeping and Portrait prompts from the seed, as earlier prompt migrations do.
- **Eval.** One new Understanding Eval case in the seed: the made-up User has a waiting guess Curiosity, "their mum lives in Singapore", and mentions their mum. Expect Get curious, checking it gently, never stating it as fact. **Don't run it**; Evals cost money and the owner decides when. Get curious comes from issue 03, which may not be merged yet; the case only names it.

## Parallel work: avoid clashes

Issue 03 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 03 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Files:** you own the Curiosity-keeping and Portrait prompts in the platform settings seed. 03 owns the Needs and Moves seeds.
- **Understanding Eval cases seed:** both add cases at the end. When rebasing, keep both.

## Acceptance criteria

- [ ] The Curiosity-keeping prompt asks for look-backs as above; the Portrait prompt no longer asks for open questions and keeps only what Zeph is fairly sure of
- [ ] The migration reloads both prompts from the seed (test, as for earlier prompt migrations)
- [ ] A test with the scripted chat model shows the keeping step's look-back saved with its not_before and sensitivity
- [ ] The guess Understanding Eval case is in the seed, with a made-up guess Curiosity, and loads; it is not run
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] `/run`: in the running app, end a real Conversation where the User vents and Zeph only listens, and see a look-back Curiosity saved with not_before at least the next day. See the rewritten Portrait has no open questions. Shift timestamps instead of waiting

## Blocked by

- `.scratch/get-curious/issues/02-curiosity-guesses.md`

## Comments
