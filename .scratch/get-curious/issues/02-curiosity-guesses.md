# 02 — Curiosity guesses

Status: ready-for-agent

## Parent

`.scratch/get-curious/PRD.md`

## What to build

A Curiosity can hold a **guess**: something Zeph suspects about the User but isn't sure of (e.g. "their mum lives in Singapore"), with **how sure** it is (low, medium or high). See ADR-0017 and the Curiosity entry in CONTEXT.md.

- **Keeping.** When a Conversation ends, the Curiosity-keeping step may write a guess for something the User hinted at without settling, or something Zeph may have got wrong. It closes a waiting guess once the User answered it in that Conversation. The usual Memory Item keeping saves what they said, so the answer is never written as a new guess.
- **Showing.** The Understanding sees a due guess Curiosity with its guess and how sure Zeph is, marked as not known and to be checked gently. When one is raised, in a reply or in the Curiosity Check-in, the reply or Check-in is told it's a guess to check, never a fact to state.
- **Limits.** Guesses share the existing Curiosity waiting limit and per-Conversation raise limit.
- **Privacy.** Users never see guesses. Delete My Data, Account Deletion and deleting the source Memory Item or Life Thread remove them, as for any Curiosity. No new guesses are made while User Memory or Curiosities don't work for the User.

The Curiosity-keeping prompt is reloaded from the seed by the migration, as earlier prompt migrations do.

## Parallel work: avoid clashes

Issue 01 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 01 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Understanding code:** you own how due Curiosities are written out for the Understanding and the reply, and the Curiosity Check-in wording. Don't touch which Moves are offered or how Moves are recorded; 01 owns that.
- **Platform settings seed:** you edit the Curiosity-keeping prompt (and any Curiosity wording shown to the Understanding or reply). 01 edits only the Woven-in Check-in wording.
- **Models and tables:** you change Curiosity only; 01 changes Move.
- Issue 04 later also edits the Curiosity-keeping prompt (look-backs). Leave a clean place for it; don't add look-backs here.

## Acceptance criteria

- [ ] Curiosities have optional guess and how-sure fields, added by a migration; plain Curiosities leave both empty
- [ ] The Curiosity-keeping prompt explains guesses and asks for them in its JSON shape; the migration reloads it from the seed
- [ ] A guess from the keeping step is saved with how sure Zeph is (Conversation-end test with the scripted chat model)
- [ ] An answered waiting guess is closed by the keeping step
- [ ] A due guess is shown to the Understanding as a guess with how sure Zeph is, to check gently (webhook test)
- [ ] A raised guess tells the reply to check it, never state it; the Curiosity Check-in does the same
- [ ] No guesses are made while User Memory or Curiosities don't work for the User
- [ ] Delete My Data and deleting the source Memory Item remove guesses (test)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] `/run`: in the running app, end a real Conversation where the User hints at something without settling it, and see a guess saved in the curiosities table. Then, in a new Conversation, the Understanding call shows it as a guess, and the User's answer closes it at that Conversation's end. Shift timestamps instead of waiting for the quiet gap

## Blocked by

None - can start immediately.

## Comments
