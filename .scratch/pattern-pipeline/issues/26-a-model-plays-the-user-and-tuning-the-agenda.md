# 26 — A model that plays the User, and tuning the Agenda's prompts from what the Evals show

Status: needs-info
Track: B
Blocked by: 25 (needs a grilling session first, see below)

## Parent

`.scratch/pattern-pipeline/PRD.md` (the Agenda and Explorations, the Evals section; decision 24 in `.scratch/pattern-pipeline/grill-decisions.md`). Design: `docs/pattern-pipeline/README.md`. What each Eval can and can't show: `docs/pattern-evals/README.md`. Raised by the owner on 25 Nov 2026, after issue 19: these two things were left out of issue 25 on purpose, to be decided with the owner.

## Needs a grilling session before any solution

Don't plan or build this yet. Run `/grilling` (or `/grill-with-docs`) with the owner first, and record the decisions here and in `CONTEXT.md` and ADRs. Only then write the plan and set this to `ready-for-agent`. The grill may split this into two issues. Open questions are listed below.

## The problem

Two gaps are left once issue 25 is built.

**1. Nothing tests the Agenda over time, with a User who answers.**

- The Whole-pipeline Eval (issue 19) runs the Agenda, but its User is a script: the texts are written into the case, so they never answer Zeph's aimed Curiosities or Thought Experiments. The counter-test is met by a scripted "it doesn't happen with…" story, not by Zeph asking (issue 20, section 19).
- Issue 25 checks one Message at a time: is the aimed question picked and asked well, and is one answer read right. It can't show the loop: ask, get an answer, judge the try, come back a different way, rest, wake.
- A model that plays the User from a hidden brief could answer Zeph, so the loop runs for real. It costs more and varies more from run to run, and a model playing a User and a model tagging them tend to agree, so it still catches breakage, not truth.

**2. There is no agreed way to change the Agenda's prompts when a case shows them going wrong.**

- Issue 25 only logs what its cases find (in `20-findings-for-the-owner.md`); it changes no prompt.
- The Agenda's own questions are written by code (`aimed_question` in `src/companion/core/agenda.py`), not a model. What a model does with them is set by `reply_plan_prompt`, the response prompt and `pattern_tagging_prompt`, which many other things depend on.
- So a fix for the Agenda can break something else, and each try costs an Eval run.

## Open questions for the grill

A model that plays the User:

1. What is it for: testing the Agenda loop only, or replacing the scripted texts in the Whole-pipeline Eval too?
2. What does the player know? The hidden true Pattern Types, a life story, how open or guarded they are? Does it ever see the Pattern Catalog (which would make it agree with the tagger even more)?
3. Which model plays, and is it a different one from Zeph's and the tagger's, to agree less? Who pays attention to its cost?
4. How does a case end: a fixed number of Conversations and texts, or when the player has nothing more to say? What stops a run that goes on too long?
5. What is checked and what passes? The same ready-and-true rule as issue 19, or Agenda things too (a counter-test asked and answered, tries judged right, never two Conversations in a row, resting after tries with nothing)?
6. Results vary run to run. How many Repeats before a result is trusted, and what does that cost?
7. Is the player's prompt an Admin setting (like the Judge's prompts), so the owner can read and change it?
8. Is this a new Eval kind, or a switch on Whole-pipeline cases (scripted or played)?
9. What must the guide say it can't show?

Tuning the Agenda's prompts:

10. Which prompts may be changed for the Agenda's sake, and who decides: the owner by hand on the Dashboard, or an agent proposing a Variant?
11. What is the routine? E.g. a failing case in issue 25's set → a Variant with the changed prompt → run only those cases plus which others → Make Live only if nothing else got worse.
12. Which other Evals must be run to show nothing else broke (Understanding, Persona, Tagging), and what does that cost each time?
13. When is a failing case the prompt's fault, and when is the case or the rule in code wrong?
14. Should any of the wording code writes today (`aimed_question`) become an Admin setting, so it can be tuned without a deploy?
15. How are findings from issue 25's first run brought in here?

## Acceptance criteria

To be written after the grill.

## Comments
