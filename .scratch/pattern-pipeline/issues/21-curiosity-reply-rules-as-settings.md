# 21 — Admins set two of the Curiosity reply rules

Status: ready-for-agent
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

- [ ] An Admin can set "Most Curiosities per reply" on the Platform Settings page; it starts at 1 for existing and new installs
- [ ] An Admin can turn "Hold a Curiosity when the reply asks why" on or off; it starts on
- [ ] With the number at 2 (and the per-Conversation limit raised to match), a reply can be given two Curiosities; at 1 it gets at most one
- [ ] With the second setting off, a reply that asks why can also carry a picked Curiosity; with it on, the Curiosity is dropped and stays due
- [ ] No Curiosity is offered while the User is struggling, whatever the two settings say
- [ ] The Model Call Log's "Curiosities offered" and "Curiosity asked" still match what happened
- [ ] `docs/message-pipeline/README.md` and `CONTEXT.md` say which rules are settings and which are fixed
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments
