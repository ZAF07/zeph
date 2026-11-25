# 33 — Understanding Eval cases that fail for old reasons

Status: ready-for-agent
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Found by issue 29 (archived: `archive/29-understanding-eval-eight-failing-cases.md`), which has every Eval Run ID.

## Why

Issue 29 ran 8 failing Understanding Eval cases on main before issue 01 (2ffa403) and on main now. None was found to have got worse because of issues 01 and 02 (two tries a side). But six of them fail often for reasons that were there before, and they still fail today. Each wastes Eval money and hides real changes. For each one the owner has to say which is wrong: the case or Zeph.

## The faults

Passes are counted over all tries in issue 29, before and now together.

1. **`small-talk-makes-no-move`: 0 of 4.** The case expects no Move for small talk (a cat knocked coffee on the keyboard). The Reply Plan always picks one: Suggest before (a tip for the keyboard), Get curious now (asks about the cat). Just chatting allows Suggest, Research and Get curious, and nothing in the Reply Plan prompt says when to make no Move. Decide: is a light Move fine in small talk (change the case), or should the prompt say when to just respond?
2. **`next-move-held-then-made`: 0 of 4.** On "where do I even start" with hosting, the case expects Zeph to hold Research for the next reply. The Reply Plan leads with Research at once and has Plan steps in mind next, every time. On the second Message it led with Suggest and supported with Research in 2 of 4. Researching at once looks like the better reply, so the case is likely out of date. Decide, then rewrite the case.
3. **`strong-mood-unknown-cause`: 1 of 4.** The case expects the Reply Plan to set "ask why". It leads with Get curious instead and the reply still asks what is behind the mood (the judge passed the reply 4 of 4). Two ways to ask the same thing, and the check accepts only one. Decide: accept either, or have the prompt say which one to use when a feeling stands out and the cause isn't known.
4. **`check-in-not-now-while-asking-for-help`: 5 of 12.** She asks for help wording a message to her landlord and a Check-in is due. The Reply Plan weaves in the follow-up ("how did Thursday's presentation go?") in more than half the tries, before and now, though the prompt says to leave it when they "asked something that needs your full answer". This one is Zeph's fault, not the case's. A stronger line in the Reply Plan prompt, or a code rule (no Check-in woven in under Advice), would fix it.
5. **`no-knowledge-for-a-vent`: 1 of 4.** The Need (Be heard) and no Knowledge are right every time. The reply fails the judge rule "no fixing": it tells her to take a slow breath or put the phone down. Zeph's fault, in the reply: under Be heard a reply shouldn't hand out a technique.
6. **`guess-checked-gently`: passes 3 of 4; the fail is a reply that stated a guess as fact.** With the case fixed by issue 29, one reply said "how's she doing back in Singapore — is that home for her these days?" and asked two questions. The Curiosity line says "Check it gently; never state it as fact". Zeph's fault, in the reply. It may belong with issue 27 (replies that mislead the User).

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

### 25 Nov 2026: the owner's decisions, the runs and what changed

**Answer: all six now pass at least 3 of 4 tries on production's prompts.** Three cases were rewritten (1, 2, 3). Three needed no change (4, 5, 6): they fail on the seed prompts but pass on the prompts production runs. No prompt and no reply code was changed.

**The owner's decisions (25 Nov)**

- 1, small talk: change the case. A light Move is fine.
- 2, hosting: rewrite the case. Researching at once is fine.
- 3, strong mood: no pick between the two choices. The owner said instead: use production's prompts from now on, for this and for 1 and 2, and allowed read-only access to production. So all six were first run on production's prompts, and 3 was settled from that run (below).
- Eval money: up to S$1.00 in total without asking again. Spent: **S$0.45**.

**How it was run**

- This worktree's own stack at main 7d63922f, plus this branch's changes for the second set of runs.
- Production's five edited prompts (`reply_plan_prompt`, `understanding_prompt`, `persona`, `persona_outlook`, `response_prompt`) were read over `ssh zeph-deploy` and written into this worktree's database only; their hashes matched production's. Production was only read. Its Needs and Moves were compared too: same text as the seed.
- Model: `deepseek/deepseek-v4.1-flash-1017` (S$0.38 in, S$1.54 out per 1M tokens). The estimate shown before each run was S$0.04 to S$0.07.

**Eval Runs** (cost worked out from each run's tokens)

| Run | Cases | Passed | Tokens in / out | Cost |
| --- | --- | --- | --- | --- |
| `953614b5-7b0e-45c2-a80b-5023579626de` | the six, as they were | 3 of 6 | 130,451 / 11,563 | S$0.067 |
| `bfdbcbd6-a151-4c16-b0c5-5d9dd445db74` | the six, as they were | 3 of 6 | 131,482 / 13,114 | S$0.070 |
| `e67c81e9-38d7-4863-a63c-16ce0fc0ff89` | the six, as they were | 2 of 6 | 131,890 / 13,657 | S$0.071 |
| `c947bc21-9afe-4cd3-94ef-214649b3703d` | the six, as they were | 3 of 6 | 132,159 / 12,081 | S$0.069 |
| `03f0935a-26bc-4463-a187-39d69b1a18e2` | the three rewritten | 2 of 3 | 81,815 / 7,129 | S$0.042 |
| `3b8dc54e-3f78-4d46-b5b0-379b435d2bb6` | the three rewritten | 3 of 3 | 81,595 / 7,241 | S$0.042 |
| `1a2256f5-31e9-40f7-b2dc-1ee55becb588` | the three rewritten | 3 of 3 | 87,999 / 6,620 | S$0.044 |
| `7a565d1a-b2de-4bc6-9b64-e9e6093af636` | the three rewritten | 3 of 3 | 81,338 / 5,930 | S$0.040 |

The runs live in this worktree's database, which is deleted at teardown. The reports were read first; what matters is below.

**Each fault, on production's prompts**

| # | Case | As it was | Now | What was done |
| --- | --- | --- | --- | --- |
| 1 | `small-talk-makes-no-move` → `small-talk-stays-light` | 0 of 4 (led with Get curious every time) | 4 of 4 | Rewritten. It no longer expects no Move. It expects Just chatting and the new judge rule `keeps_small_talk_light`: light and short, a joke or light question is fine, no tips for the keyboard, not turned serious. |
| 2 | `next-move-held-then-made` → `hosting-help-over-two-messages` | 0 of 4 (no Research held; it researched at once) | 3 of 4 | Rewritten. First Message: Advice or Accountability and a lead Move. Second Message: a lead Move and the rule `names_hosts_under_budget`, so Research may lead or support. The one fail is the rule doing its job: the reply named one host under budget and one over it. |
| 3 | `strong-mood-unknown-cause` | 0 of 4 ("ask why" never set; led with Get curious) | 4 of 4 | `asked_why: true` removed; the rule `gentle_probe` stays. The reply asked what is behind the mood 8 of 8 times. Production's prompt says "Do not ask why reflexively", so the Reply Plan uses Get curious for this, and the case now checks what the person gets, not which of the two ways was used. |
| 4 | `check-in-not-now-while-asking-for-help` | 4 of 4 | not run again | Left as it is. The Check-in was never woven in. |
| 5 | `no-knowledge-for-a-vent` | 3 of 4 | not run again | Left as it is. No breathing tip in any try. The one fail was a silver lining ("the mistake wasn't anywhere near as bad as the moment made it feel"), a real fault in the reply. |
| 6 | `guess-checked-gently` | 4 of 4 | not run again | Left as it is. Every reply asked "Where's home for her these days?" and never said Singapore. |

**What was built**

- `src/companion/seed/evals/cases/understanding.yaml`: the three cases and the rule `keeps_small_talk_light`. Two cases got new keys, since the old names said the opposite of what they now check.
- Migration `0103_understanding_cases_follow_the_reply.py` calls `reload_eval_case_unless_edited` for the three old keys, so stacks that already hold them get the new ones. A case an Admin edited or archived is kept, with a warning in the backend log.
- `tests/test_understanding_eval_helpers.py`: the seed-case tests follow the new cases.
- Shared files touched: one migration (0103).

**For the owner to know**

- **The seed prompts and production's prompts give different results.** Faults 4, 5 and 6 were found on the seed prompts (issue 29). On production's prompts they don't show. A local stack or a new worktree runs the seed prompts, so its Evals don't tell you what production does unless production's prompts are loaded first, as here.
- **After the next deploy, fault 4 may come back for a while.** That deploy replaces production's Reply Plan prompt with the seed's until you merge your edit back (see `prod-prompt-copies/README.md`). The seed's Reply Plan wove the Check-in into a request for help in more than half the tries. Merging your edit back should end it.
- **Open question: should the seed take production's wording?** Not done here. Production's Reply Plan prompt has no rules for the new fields (Curiosity pace, Pattern sharing), so it can't replace the seed as it is.
- **"Ask why" is hardly used on production's prompt**: set 0 of 8 times here. No seed case expects it set any more.
- The two renamed cases start with no run history, and move to the end of the Understanding list.
- The copies of production's prompts used here were kept only in the session's temp folder, not in the repo.
- `20-findings-for-the-owner.md` was not edited (other agents work in it).
