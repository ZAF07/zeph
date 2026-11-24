# 20 — Bugs, risks and failures found while building the pattern pipeline

Status: needs-triage
Track: shared
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17, 18, 19

## What this is

The final issue of the pattern-pipeline PRD (`.scratch/pattern-pipeline/PRD.md`). While agents work on the other issues of this PRD, they log here every bug, risk, failure or potential failure they find that their own diff doesn't fix. Once the other issues are done, the owner and an agent work through the list together.

Log only:

- **bug**: something that behaves wrongly today;
- **failure**: a check, test, Eval or tool that fails;
- **risk / potential failure**: something that works today but can go wrong for Users, data or cost.

Don't log notes about how your own work went.

## When you finish an issue of this PRD

Before archiving, ask: did I find a bug, failure, risk or potential failure, in my task or outside it, that my diff doesn't fix? Add one section for your issue above `## Comments`, in issue order, with one entry per finding:

```markdown
## NN — <issue title> (<YYYY-MM-DD>)

### <short title>

- **Kind:** bug | failure | risk | potential failure
- **What:** one or two sentences, with evidence (file:line, commit, Eval Run, output).
- **Impact:** what goes wrong, and for whom.
- **Suggested fix:** one concrete action, and roughly what it costs.
```

If there is nothing, the section holds one line: "Nothing found."

## 02 — Test the water, pace and backing off (2026-11-24)

### Picked Curiosities left out by the Reply, still marked raised

- **Kind:** bug
- **What:** in the live `/run`, the Reply Plan picked a Curiosity 9 times; in 3 of them, Zeph's messages never asked it (run 1 A1 and C1, run 3 D5). Each was still marked raised, so it is never asked again. Before commit 55c03b8, the next Reply Plan also called the unasked Curiosity "brushed off", which counts toward backing off. Now it is told to answer null if the Curiosity was never asked, but that wasn't seen live.
- **Impact:** Curiosities get used up without being asked, and a wrong brush-off can make Zeph back off a User for no reason.
- **Suggested fix:** after the reply, check whether the picked Curiosity was really asked, like the check that takes back a woven-in Check-in the reply left out. Mark it raised only when it was asked. One small model call per reply that picks a Curiosity.

### 8 Understanding Eval cases fail, cause unknown

- **Kind:** failure
- **What:** the whole Understanding Eval on main after issue 02 passed 22 of 30 (S$0.21). The failing cases:
  - `strong-mood-unknown-cause`
  - `knowledge-for-a-reflective-question`
  - `no-knowledge-for-a-vent`
  - `check-in-not-now-while-asking-for-help`
  - `internal-testing-finish-line`
  - `small-talk-makes-no-move`
  - `next-move-held-then-made`
  - `guess-checked-gently`

  There's no run from before issues 01 and 02 to compare against, and both of them reloaded `reply_plan_prompt`.
- **Impact:** a regression in how Zeph picks Needs and Moves, or weaves in Check-ins, may already be on main unnoticed.
- **Suggested fix:** run those 8 cases twice each on main as it was before issue 01's merge (2ffa403) and on main now, about S$0.20, then fix what really got worse.

### An Eval case that can't pass reliably

- **Kind:** failure
- **What:** `guess-checked-gently` expects the reply to lead with Get curious and to check the guess. When the Reply Plan asks the guess's Curiosity, the rule "one question per reply" from issue 01 drops Get curious. It failed in all 3 tries, each time for a different reason.
- **Impact:** a flaky case hides real changes and wastes Eval money.
- **Suggested fix:** change its expectation, for example to "Curiosity raised" instead of "lead Move Get curious". One case edit and an S$0.01 run.

### Curiosity Check-ins ignore pace and backing off

- **Kind:** risk
- **What:** the "Something I've been wondering" Check-in sends a Curiosity under its own weekly limit, even while Zeph is backing off in replies.
- **Impact:** a User who just brushed off two questions can get a Curiosity Check-in the next day.
- **Suggested fix:** if backing off should hold Check-ins too, call `may_offer_curiosity` (`core/curiosity_pace.py`) from the Check-in decision.

### Dropped topics can still come back through follow-up questions

- **Kind:** potential failure
- **What:** a Curiosity the User asked to drop is never offered again, and no new one is made on that topic. But the Reply Plan, and its Get curious questions, aren't told which topics were dropped.
- **Impact:** Zeph can ask about something the User asked it to drop, breaking their boundary.
- **Suggested fix:** show the Reply Plan the dropped topics as "don't ask about". It needs a reload of `reply_plan_prompt`, so it's best bundled with the next change to that prompt.

### Migrations overwrite Admin prompt edits

- **Kind:** risk
- **What:** migrations 0073, 0078, 0080 and 0081 drop a stored prompt so it reloads from the seed, even where an Admin edited it.
- **Impact:** with real Users on prod, an Admin's prompt tuning is lost on deploy, and nothing says so.
- **Suggested fix:** drop a stored prompt only when it still equals the previous seed text; otherwise keep it and log a warning that it needs updating by hand.

### Eval environment copies fields by hand

- **Kind:** risk (one bug found and fixed)
- **What:** `adapters/evals/environment.py` copied Moves into the Eval database without `asks_a_question`. So in Eval Runs, issue 01's one-question rules and issue 02's follow-up cap did nothing. Fixed in c2351af; Needs are copied in full today.
- **Impact:** any new column on Needs, Moves or settings can silently go missing in Evals, so Evals pass or fail on something other than the live app.
- **Suggested fix:** use the Postgres repositories' row mapping in the Eval environment, or add a test that every Move and Need field survives the copy.

### Dashboard Docker build fails on the first try

- **Kind:** failure
- **What:** `make restart` failed at `pnpm build` ("Build failed because of webpack errors") on the first build in two fresh worktrees; a plain retry passed both times. Cause not found.
- **Impact:** agents lose time and may think their change broke the build. A deploy could fail the same way.
- **Suggested fix:** keep the full build log on the next failure. Fetching fonts with `next/font/google` during the build is the first suspect.

## Comments
