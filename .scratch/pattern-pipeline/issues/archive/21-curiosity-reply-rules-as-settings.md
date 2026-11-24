# 21 — Admins set two of the Curiosity reply rules

Status: completed
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Follow-up to issue 01 (`issues/archive/01-needs-say-how-curiosities-are-treated.md`), which fixed these rules in code. Design: `docs/pattern-pipeline/README.md`.

## What to build

Issue 01 put three Curiosity rules in code. Two of them become Platform Settings an Admin can change on the Dashboard:

1. **Most Curiosities per reply.** A number, starting at 1. Today it is `MOST_CURIOSITIES_PER_REPLY` in `core/reply_plan.py:81`.
2. **Hold a Curiosity when the reply asks why.** On or off, starting on. Today `settle_curiosities` (`core/reply_plan.py:859`) always drops the picked Curiosity when the reply asks why the User feels as they do.

The third rule, no Curiosity while the User is struggling, stays fixed in code.

Both settings start at today's behaviour, so nothing changes for Users until an Admin changes one. Follow how the other Curiosity settings are wired (`curiosity_replies_between`: `seed/platform_settings.yaml`, `core/platform_settings.py`, `web/src/components/PlatformSettingsForm.tsx`).

Things to settle while building:

- `curiosities_per_conversation` (now 1) still caps the per-reply number. The setting's help text should say so.
- The Reply Plan prompt says how many Curiosities it may pick. If the number is written into `reply_plan_prompt`, it must come from the setting, not be typed in the prompt.
- With the second setting off, a reply can hold two questions. The Reply's wording for a picked Curiosity may need to say how to place it beside the "why" question.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] An Admin can set "Most Curiosities per reply" on the Platform Settings page; it starts at 1 for existing and new installs
- [x] An Admin can turn "Hold a Curiosity when the reply asks why" on or off; it starts on
- [x] With the number at 2 (and the per-Conversation limit raised to match), a reply can be given two Curiosities; at 1 it gets at most one
- [x] With the second setting off, a reply that asks why can also carry a picked Curiosity; with it on, the Curiosity is dropped and stays due
- [x] No Curiosity is offered while the User is struggling, whatever the two settings say
- [x] The Model Call Log's "Curiosities offered" and "Curiosity asked" still match what happened
- [x] `docs/message-pipeline/README.md` and `CONTEXT.md` say which rules are settings and which are fixed
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments

- **Design (24 Nov 2026).** No reference file was added and no pixel test run. Platform Settings has no reference of its own. It is built from the `AdminPersona` form template, which already draws a switch field row (the "Web search" row). `web/design/README.md` says agents never edit `reference/`, and that template pages are compared by eye at 1280 and 390. That was done in `/run`: the two rows look like the template's number and switch rows at both widths.
- **Prompt.** `reply_plan_prompt` no longer says "At most one per reply". The number comes from the setting, in the due Curiosities' header ("at most N in this reply"). "ask by default: pick one" became "pick one, or more when the list allows more and they fit the moment", because a live run at 2 per reply showed the model always picked exactly one. Migration 0084 reloads the prompt from the seed. **This drops any Admin edit to it**, the same as 0081.
- **Persona clash (from code review).** The Persona says "Ask at most one question". When a reply asks more than one question this way (two Curiosities, or one beside asking why), the Reply's Curiosity section now says that more than one is fine this time. Before this note, a live run asked only one of two picked Curiosities. After it, it asked both.
- **Known limits.** "Curiosity asked" in the Model Call Log is still yes/no, not a count. A picked Curiosity the Reply leaves out is still marked raised, as before this issue. Per-reply 2 makes that a bit more likely.

### Evidence (`/run`, worktree stack, 24 Nov 2026)

- New install: the fresh database migrated to 0084 with `curiosities_per_reply = 1` and `curiosity_held_when_asking_why = true`.
- Existing install: the database was taken back to 0083, both keys deleted, and `reply_plan_prompt` edited. After a backend restart it was at 0084, both keys were back at 1 / true, and the prompt was reloaded from the seed.
- Dashboard (Admin, Playwright): the Curiosities section showed "Most Curiosities per reply" at 1 and "Hold a Curiosity when the reply asks why" on, each with its hint, at 1280 and 390. Saved per Conversation 2, per reply 2 and holding off. After a reload it showed 2 and off, and the rows in `platform_settings` had `updated_by` set. No page errors.
- Chat, real DeepSeek model, logging chat channel. In the unscripted runs at 2/2 the Reply Plan was told "(raised 0 of at most 2 in this Conversation; at most 2 in this reply)". The model picked one, and the log said offered 2, asked yes, matching the one raised. For the scenarios below, the real app ran in the backend container on the real database and model, with only the Reply Plan's Curiosity picks (and ask_why) overridden:
  - A, 2 per reply, picks both: both kept in the form, both raised, log offered 2 / asked yes. Zeph asked "how the climbing trip with Sam went" and "what did the puppy end up being called?"
  - B, 1 per reply, picks both: one kept and raised, the other waiting. Log offered 2 / asked yes.
  - C, holding off, asks why plus a Curiosity: `asked_why` true, Curiosity kept and raised, the reply told to ask why first. Zeph asked both: "What's the flatness like, actually? … And did the climbing trip with Sam happen?"
  - D, holding on, same picks: Curiosity dropped, `curiosity_not_asked_why` = "The reply asks why they feel as they do instead.", both still waiting. Log offered 2 / asked no.
  - E, struggling, with 2 per reply and holding off: offered 0, none raised, both waiting. Log offered 0 / asked no.
- Checks on the final code: `pytest` 1899 passed, `ruff check`, `ruff format --check` and `mypy src` clean, and `pnpm lint`, `format:check`, `typecheck` and `test` (933 passed) clean.
- Docs: `docs/message-pipeline/README.md` (the Built 24 Nov paragraph) and `CONTEXT.md` (Curiosity) say which two rules are settings and which stay fixed in code.

## Completion

- Completed: 2026-11-24
- Commits (branch `pattern-21-curiosity-settings`):
  - `ecee2af` Admins set most Curiosities per reply and holding one when the reply asks why
  - `f5e9370` Review fixes: tell the Reply when more than one question is fine; clearer names
  - `0eec472` Docs: the reply is told when more than one question is fine
  - `74ba573` updated tasks status
- Merged into `main`: `9421a48` Merge issue 21: Admins set two of the Curiosity reply rules
