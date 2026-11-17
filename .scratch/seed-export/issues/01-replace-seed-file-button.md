# 01 — "Replace Seed file" button for Admins

Status: needs-info
Lane: solo

> **Before any work: run `/grill-with-docs` on this issue with the owner.** The owner asked for this to be grilled when it is picked up again. Don't start building from this file as it stands. The decisions below are still open, and the grilling should settle them, update `CONTEXT.md`/ADRs, and then this issue (or a PRD and issues) gets rewritten as `ready-for-agent`.

## Parent

None yet. Raised by the owner on 2026-11-17, right after Moves issue 01.

## Problem

Admins tune wording and data on the Dashboard: the Persona, prompts, Needs, Moves, and so on. The seed files under `src/companion/seed/` only hold the defaults, and they are used again when:

- a fresh install loads them (first run only),
- a migration reloads settings from them. Migration 0050 (Moves) did this: it overwrote the Persona, the Understanding prompt, the web search wording, and Advice/Accountability "how to reply" with the seed text,
- the Eval and test environments are set up.

So wording an Admin tuned and liked can be lost, or never become the new default.

## What the owner wants

A button on the admin Dashboard called **Replace Seed file**. When an Admin presses it, the seed file is replaced with what is currently saved in the database. The tuned values then become the new defaults, and can be committed.

## Open questions (for the grilling)

1. **Where does it write?** The backend runs in Docker, and the seed files are copies baked into the image. Writing there changes nothing in the repo and is lost on the next rebuild. Options:
   - **Download / show the changes** (agent's lean): the button hands over the seed files, or a diff, and someone drops them into the repo and commits. This also works once the app is hosted, where there is no repo.
   - **Write into the repo**: the backend container mounts the repo's seed folder. This only works locally, and it leaves uncommitted changes in the main folder while other agents work there.
2. **Comments in the seed files.** They carry the explanations, e.g. "Any change must keep the honesty rules". A plain YAML writer drops every comment. Should they be kept (a comment-keeping writer), and how are comments for new keys handled?
3. **Which data?** Platform Settings, Needs (with ruled-out Moves), Moves, Memory Categories, Check-in Kinds, Helplines, Knowledge (starter set), Eval Cases, Judge settings? Never anything about Users or their memories.
4. **All at once, or per section?** One button for everything, or one per area (e.g. "Needs and Moves", "Prompts")?
5. **Who and how safe?** Admins only. A confirmation step? A preview of what changes before it's replaced?
6. **What about migrations that reload from the seed** (like 0050)? Once tuned values live in the seed, should future wording changes be merged with Admin edits instead of overwriting them?
7. **Is a new domain term needed** (e.g. what the "defaults" are called) in `CONTEXT.md`, and an ADR for where seed data comes from?

## Acceptance criteria

To be written after the grilling.

## Blocked by

None. Waiting on the owner's grilling session (`/grill-with-docs`).
