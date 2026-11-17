# 01 — Moves shape replies

Status: ready-for-agent
Lane: solo (lands before any other Moves issue)

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **This issue runs alone and must be merged to main before Lane A (02, 03, 06, 07) and Lane B (04, 05, 08) start.** Keep it to what's below, so both lanes build on one shared base.

## What to build

The tracer bullet. The Companion picks Moves before each reply, and they change what it does.

- Moves exist as Admin-managed data (ADR-0004, ADR-0016): name (unique ignoring case), when it fits, how to do it, list position. Starter Moves in the seed: Calm, Ground, Reframe, Mirror, Suggest, Plan steps, Push, Research.
- Each Need has ruled-out Moves. Starter rule-outs in the seed: Be heard rules out Reframe, Suggest, Plan steps, Push, Research; Think it through rules out Suggest, Research; Just chatting rules out Calm, Ground, Reframe, Mirror, Plan steps, Push; Get it done and Ask more rule out all.
- A migration adds the starter Moves and rule-outs to a database that has Needs but no Moves (follow the Check-in Kinds migration).
- The Understanding is shown the Moves each Need allows and picks a lead Move and at most one supporting Move, or none. An unknown or disallowed Move is dropped. The fallback Understanding has no Moves.
- The lead and supporting Moves' "how to do it" go into the reply guidance after the Need's "how to reply".
- Understandings store the lead and supporting Move names. The Model Call Log shape shows them (never content for Users).
- Seed wording (these are the defaults): the Persona says the Companion has real views and says them, and is here to help the User grow and get unstuck (keep "follow their lead" for topics); the web search tool description drops "not for advice" and allows practical requirements such as a budget in queries, never personal details; the Understanding prompt explains Moves; any Need wording needed to separate stance from action.

No Admin page yet (issue 02). Web tools stay offered on every reply as today.

## Acceptance criteria

- [ ] Starter Moves and rule-outs load on a fresh install, and the migration adds them to an existing database with no Moves (and adds nothing when Moves exist).
- [ ] A Telegram Message read as Be heard is never given Push, Suggest, Plan steps, Research or Reframe; a disallowed or unknown Move in the model's answer is dropped.
- [ ] The picked lead and supporting Moves' "how to do it" reach the reply instructions.
- [ ] Understandings store the Moves, and the Model Call Log shows their names without content.
- [ ] Seed Persona, web search tool description, Understanding prompt and Needs carry the new wording.
- [ ] Tests at the Telegram webhook seam (prior art: the Understanding tests) and the migration seam; `pytest`, `ruff`, `ruff format`, `mypy` pass.
- [ ] `/run`: in the running app, the hosting chat from the PRD leads to a Research or Suggest Move and a reply that names real options.

## Blocked by

None - can start immediately
