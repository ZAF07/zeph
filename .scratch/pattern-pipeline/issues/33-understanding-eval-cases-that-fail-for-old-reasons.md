# 33 — Understanding Eval cases that fail for old reasons

Status: needs-triage
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Found by issue 29 (archived: `archive/29-understanding-eval-eight-failing-cases.md`), which has every Eval Run ID.

## Why

Issue 29 ran 8 failing Understanding Eval cases on main before issue 01 (2ffa403) and on main now. None got worse because of issues 01 and 02. But six of them fail often for reasons that were there before, and they still fail today. Each wastes Eval money and hides real changes. For each one the owner has to say which is wrong: the case or Zeph.

## The faults

Passes are counted over all tries in issue 29, before and now together.

1. **`small-talk-makes-no-move`: 0 of 4.** The case expects no Move for small talk (a cat knocked coffee on the keyboard). The Reply Plan always picks one: Suggest before (a tip for the keyboard), Get curious now (asks about the cat). Just chatting allows Suggest, Research and Get curious, and nothing in the Reply Plan prompt says when to make no Move. Decide: is a light Move fine in small talk (change the case), or should the prompt say when to just respond?
2. **`next-move-held-then-made`: 0 of 4.** On "where do I even start" with hosting, the case expects Zeph to hold Research for the next reply. The Reply Plan leads with Research at once and has Plan steps in mind next, every time. On the second Message it led with Suggest and supported with Research in 2 of 4. Researching at once looks like the better reply, so the case is likely out of date. Decide, then rewrite the case.
3. **`strong-mood-unknown-cause`: 1 of 4.** The case expects the Reply Plan to set "ask why". It leads with Get curious instead and the reply still asks what is behind the mood (the judge passed the reply 4 of 4). Two ways to ask the same thing, and the check accepts only one. Decide: accept either, or have the prompt say which one to use when a feeling stands out and the cause isn't known.
4. **`check-in-not-now-while-asking-for-help`: 5 of 12.** She asks for help wording a message to her landlord and a Check-in is due. The Reply Plan weaves in the follow-up ("how did Thursday's presentation go?") in more than half the tries, before and now, though the prompt says to leave it when they "asked something that needs your full answer". This one is Zeph's fault, not the case's. A stronger line in the Reply Plan prompt, or a code rule (no Check-in woven in under Advice), would fix it.
5. **`no-knowledge-for-a-vent`: 1 of 4.** The Need (Be heard) and no Knowledge are right every time. The reply fails the judge rule "no fixing": it tells her to take a slow breath or put the phone down. Zeph's fault, in the reply: under Be heard a reply shouldn't hand out a technique.
6. **`guess-checked-gently`: a reply stated a guess as fact, 1 of 3.** With the case fixed by issue 29, one reply said "how's she doing back in Singapore — is that home for her these days?" and asked two questions. The Curiosity line says "Check it gently; never state it as fact". Zeph's fault, in the reply. It may belong with issue 27 (replies that mislead the User).

Two more cases were only flaky and are left alone: `knowledge-for-a-reflective-question` (3 of 4) and `internal-testing-finish-line` (2 of 4, picks a different Move or Need now and then).

## What to do

- Owner: for 1, 2 and 3, say whether the case or the prompt changes.
- A changed seed case needs a migration that calls `reload_eval_case_unless_edited` (see `src/companion/adapters/postgres/migrations/README.md`).
- A changed prompt needs a migration that calls `reload_prompt_unless_edited`.
- Evals cost money: show the owner the estimate before each run. One case is about S$0.007 a try.

## Acceptance criteria

- [ ] The owner decided 1, 2 and 3
- [ ] Each of the six passes at least 3 of 4 tries, or is recorded as left as it is, with why
- [ ] Eval Run IDs and costs are in Comments

## Comments
