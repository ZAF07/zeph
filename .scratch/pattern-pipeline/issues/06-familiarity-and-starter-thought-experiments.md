# 06 — Familiarity: Zeph knows how well it knows a User, and starts new Users with starter Thought Experiments

Status: ready-for-agent
Track: A
Blocked by: 05

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 16, 17, 18, 19, 80). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Familiarity is how well the Companion knows a User: new, getting to know, or knows well. Code works it out at each Conversation end from counts (Conversations, Life Threads, Observations from real stories, Pattern states) against Admin-set bars. The Reply Plan is told it in one line on every reply, and Admins see it for each User.

A new User is offered starter Thought Experiments in their first Conversations (start: 4 over the first 14 days, at most 1 per Conversation), under the usual Need rules. Their answers are weak evidence. Once the User is getting to know, the Agenda takes over and starter ones stop. Onboarding is unchanged.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] Familiarity is worked out by a pure function from counts and Admin-set bars, and recomputed at each Conversation end
- [ ] The Reply Plan is given the User's Familiarity in one line, and the prompt says what each level means for how Zeph asks
- [ ] A new User with Pattern exploring on is offered starter Thought Experiments within the Admin-set number, days and per-Conversation cap
- [ ] Starter Thought Experiments stop once the User is getting to know
- [ ] A starter answer alone never makes a Pattern suspected or ready
- [ ] Admins see each User's Familiarity on the Users page
- [ ] Onboarding has no new step
- [ ] Each bar and limit is a Platform Setting with a hint
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `05-thought-experiments.md`

## Comments
