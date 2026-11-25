# 20 — Bugs, risks and failures found while building the pattern pipeline

Status: needs-triage
Track: shared
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 25, 26

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

## 01 — Needs say how Curiosities are treated (2026-11-24)

### A never-Need still shows the Reply Plan the due Curiosities

- **Kind:** risk
- **What:** the Reply Plan picks the Need and the Curiosity in the same model call, so the due Curiosities can't be hidden under a Need set to never. Code drops any pick afterwards (`core/curiosities.py:243`, `settle_curiosities` in `core/reply_plan.py:859`) and logs 0 offered.
- **Impact:** the model can still shape its Moves around a Curiosity that code then drops, so the reply may lean toward a topic the Need says not to raise.
- **Suggested fix:** pick the Need first, then offer Curiosities in a second step only when the Need allows them. One more small model call per reply, and a reload of `reply_plan_prompt`.

### A never-Need doesn't stop questions the reply makes up itself

- **Kind:** potential failure
- **What:** in the Eval Run for issue 01 (Understanding, case `curiosity-raised-once`), Variant B had "Just chatting" set to never: 0 Curiosities offered, yet the reply still asked about the presentation, from its memory of the week.
- **Impact:** an Admin who sets a Need to never expects no such questions (for example under "Be heard"), but the User can still get one.
- **Suggested fix:** under a never-Need, tell the Reply not to bring up open topics from memory unless the User does. A small prompt change and an S$0.01 Eval run to check it.

### Needs and Moves page hints name the wrong step

- **Kind:** bug
- **What:** the hints say "when the Understanding picks this Need" (`web/src/components/NeedFields.tsx:69`) and "this Move" (`web/src/components/MoveFields.tsx:56`). The Reply Plan picks both.
- **Impact:** Admins get a wrong picture of which step and prompt to tune.
- **Suggested fix:** change both hints to "the Reply Plan" and update the matching design reference text. A few minutes.

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

## 03 — Users set how direct Zeph is with its Read (2026-11-24)

### The Reply model doesn't reliably call change_directness

- **Kind:** failure
- **What:** across three Settings Eval runs, `more-direct` passed 1 of 3 and `gentler` passed 1 of 2 (Eval Runs 2eb36fca, 11e0451e, 29a300a8). When it failed, the reply asked a question, or said "Done — I've set myself to direct" without calling the tool. In a live `/run`, "could you go easier on me…" got "you're on gentle now" while the setting was still direct. A plainer "please change how direct you are to gentle" did call it. Every other Settings case passes. Adding "Never say you changed a setting without calling its tool" to `reply_settings_instructions` helped `more-direct` once, but didn't fix it.
- **Impact:** a User asks Zeph to be gentler or blunter, is told it's done, and nothing changes. Their Dashboard still shows the old level.
- **Suggested fix:** try the Reply with thinking on, or a stronger reply model, for replies that offer settings tools. Compare on the two cases, 3 tries each, about S$0.05.

### A tool call sent to the User as plain text

- **Kind:** bug
- **What:** in Eval Run 2eb36fca (`more-direct`), deepseek-flash wrote the tool call into its reply instead of calling it. The made-up User got the messages "<tool call>" and "<function=change_directness>\n<parameter=directness>direct</parameter>\n</function>\n</tool_call>".
- **Impact:** real Users can get raw markup in chat, and the change they asked for isn't made.
- **Suggested fix:** in the chat model adapter, catch replies that hold `<tool call>` or `<function=` markup. Run the tool from them, or retry the call once, and never send that markup. A small adapter change with a test.

### Pixel test can't run as shipped

- **Kind:** failure
- **What:** `web/design/compare.cjs` waits for `networkidle`, which Clerk's `protect.clerk.com` probes never reach, so every signed-in page times out. This check used a copy in the git-ignored `web/design/.diff/` that aborts those requests. `M-Account` passes at 0.45% (limit 0.5%). The differing pixels are in the time zone field, the sticker icons and the "Delete my data" text, none of which this issue touched.
- **Impact:** every UI issue has to patch the test by hand to get a PASS. One small change to the Account page will push `M-Account` over the limit for reasons unrelated to that change.
- **Suggested fix:** the owner adds the `protect.clerk.com` abort to `compare.cjs` and looks at why those three parts of `M-Account` drift.

### Migration 0086 overwrites Admin prompt edits too

- **Kind:** risk
- **What:** like 0073 to 0081 (see 02), 0086 drops the stored `reply_plan_prompt` and `reply_settings_instructions` so they reload from the seed.
- **Impact:** the same as in 02: Admin edits to these two prompts are lost on deploy.
- **Suggested fix:** the same as in 02.

## 11 — Tagging step keeps Observations (2026-11-24)

### Tag names written out by hand in several places

- **Kind:** potential failure
- **What:** the tag values (relationship, power, setting, stance) are written out by hand in the enums in `core/models.py`, the reader in `core/observations.py:247` and `:475`, the tagging prompt (`seed/platform_settings.yaml:1298`) and the catalog loader (`adapters/pattern_catalog.py`).
- **Impact:** if the prompt and the code drift apart, the code checks will quietly drop the model's tags. Observations then lose their tags, or are dropped, with nothing to say why.
- **Suggested fix:** build the prompt's tag lists from the enums, so the code is the only place they are written. A small change, but it needs a reload of the tagging prompt.

## 13 — "Things you said that Zeph kept" (2026-11-24)

### Seed Copy is behind the design references, so Memories pixel tests fail

- **Kind:** failure
- **What:** `src/companion/seed/copy.yaml` still has "Conversation Summaries" (`memories.tabs.summaries` and the Day Summaries heading and intro) and an older Memories hero line ("short summaries of past Conversations"), while every `Memories*` reference says "Day Summaries" / "a short account of each day you talked". In fixture mode `compare.cjs` fails Memories--tab-summaries (0.71%), M-Memories (0.91%) and M-Memories--tab-patterns (0.58%) on main, and M-Memories--tab-quotes (0.64%) on this branch, all from that text.
- **Impact:** the pixel test can't pass for those pages, so real drift on them would go unnoticed; new Users get the old wording seeded.
- **Suggested fix:** update those seed texts to the references' wording (and a migration only if the live stored slots should change too); about half an hour.

### Tagging needs Users to be told first, so Evals of tagging keep nothing

- **Kind:** potential failure
- **What:** `PatternTagger.tag_from` (`core/observations.py`) now keeps nothing until `users.pattern_noticing_told_at` is set. Eval Users made by `adapters/evals/in_process_companion.py` never press "Got it".
- **Impact:** the tagging Eval (issue 14) and the whole-pipeline Eval (19) would see no Observations and score as if the tagger found nothing.
- **Suggested fix:** set `pattern_noticing_told_at` when the in-process companion makes its Eval User, as it already does for `ai_notice_acknowledged_at`; a few lines.

### A deleted quote could come back if a Conversation is ever tagged twice

- **Kind:** risk
- **What:** the User lock covers scoring and deleting a quote, but tagging's `observations.add_many` runs outside it. Today each Conversation is tagged once, so nothing deleted can be inserted again.
- **Impact:** if Conversation ends are ever retried after tagging, or old Conversations are tagged again (e.g. when a Pattern Type is added), a quote the User deleted could be kept again.
- **Suggested fix:** before building any retagging, keep a record of deleted quotes (Conversation and quote) and skip them in `plan_observations`; about an hour.

## 14 — Tagging Eval (2026-11-24)

### Owner corrects the drafted Tagging cases

- **Kind:** risk
- **What:** The 44 Tagging cases in `src/companion/seed/evals/cases/tagging.yaml` were drafted by Claude and are the defaults until the whole PRD is built (owner's decision, 24 Nov 2026; moved here from issue 14's last criterion).
- **Impact:** Until corrected, a Tagging Eval score measures the step against Claude's labels, not the owner's.
- **Suggested fix:** Follow `docs/pattern-evals/adding-tagging-cases.md`: correct on the Dashboard, run, then have an agent copy the cases into the seed.
- [ ] Owner corrected the Tagging cases

### Tagging context lines call the User "she"

- **Fixed (24 Nov 2026):** issue 22 (`archive/22-context-lines-gender-the-user.md`).

- **Kind:** bug
- **What:** In the first Tagging Eval run (run `4352910b`, case `conf-mum-holiday-plans`) the real tagging step wrote context lines like "she spent the evening resentful" and "Explaining why she gave in". The tagging prompt doesn't ask for they/them.
- **Impact:** Context lines are shown to Users as "Zeph's note" on "Things you said that Zeph kept" (issue 13), so a User can be misgendered on their own Memories page.
- **Suggested fix:** Add one line to `pattern_tagging_prompt`: write context lines with "they/them" (or "you") and never guess a gender; add a Tagging Eval rule or a code check later. Minutes; then re-run the Tagging Eval (about S$0.15).

### First Tagging Eval run: 33 of 44 pass

- **Kind:** failure
- **What:** Run `4352910b` (24 Nov 2026, live settings, `deepseek-flash` with thinking, S$0.1476): all four "anyone would" CONF.AVOID.BELONG cases (waiter, taxi, CEO, airline queue) kept nothing; the mum case was kept as situational (code marks a parent tagged power "above" as "anyone would"); three of four unclear cases came back as one clear Observation or two separate ones instead of one unclear; CTRL "real crisis" cases were tagged "for" or nothing instead of "against" (D2). Two seed cases were wrong for code's rules and were fixed in review (`conf-against-only-with-boss`, `unclear-conf-or-ach-boss-feedback` now expect situational).
- **Impact:** Until fixed, low-stakes stranger moments are never recorded as "anyone would" (so they don't count against a Pattern), parents count as "anyone would", and look-alike Pattern Types are rarely marked unclear, so scores lean on guesses.
- **Suggested fix:** The owner corrects the drafted cases first (issue 14's open criterion), then decide per finding: say in the tagging prompt when to tag "anyone would" moments and when to write one unclear Observation; consider narrowing CONF.AVOID.BELONG's `anyone_would_when` power `above` to people outside family (new catalog version). An hour plus a S$0.15 re-run.

### The estimate for never-run Tagging cases is off

- **Kind:** risk
- **What:** New run estimated 308,000 in / 39,600 out tokens (S$0.178) for 44 Tagging cases; the run used 79,120 in / 76,318 out (S$0.148). A never-run case uses a rough per-Eval figure (`ROUGH_TOKENS_PER_CASE`, 7,000 / 900) priced on the reply model, while tagging with thinking writes far more than it reads.
- **Impact:** Small here, but a new Eval or a Variant with a dearer model can be estimated well under its real cost. After one run the estimate uses each case's real tokens, so it corrects itself.
- **Suggested fix:** Set Tagging's rough figure to about 1,900 / 1,800 and price rough figures on the model of the step each Eval runs. Under an hour.

### An unclear case matches any pair holding the expected Pattern Type

- **Kind:** potential failure
- **What:** `matches` in `core/evals/tagging_eval.py` passes an unclear expectation when the expected Pattern Type is either of the two kept, whatever the other is (a CONF/ACH case passes if CONF/CTRL is kept).
- **Impact:** A Tagging case can pass with the wrong look-alike pair.
- **Suggested fix:** If the owner wants the pair checked, add an optional "second Pattern Type" field to the expected Observation. An hour.

### `make restart` web build failed once, then passed

- **Kind:** potential failure
- **What:** In the pattern-14 worktree the first `make restart` failed in `pnpm build` ("Build failed because of webpack errors"); the next two passed with no change. The error lines weren't kept.
- **Impact:** A deploy built on the server could fail the same way now and then.
- **Suggested fix:** If it happens again, keep the full build log and look for a memory or race cause.

### The first 44 Tagging cases were written for a three-type catalog

- **Kind:** eval quality
- **What:** Issue 15 grew the catalog from three Pattern Types to fifteen. The first 44 Tagging cases expect only CONF.AVOID.BELONG, ACH.WORTH.PERF or CTRL.UNCERT.PLAN; several now also fit a new look-alike (e.g. `conf-yes-to-sister-then-resents` could read as APPR.GIVE.NEEDED). The 24 new cases (one for, one against per new type) haven't been run.
- **Impact:** A Tagging run may now fail cases where the model picks a fair new look-alike, and each run costs several times more (the whole catalog goes in every call).
- **Suggested fix:** Run the Tagging Eval once (show the estimate first), then correct expectations to "unclear" with the right pair where the new types fit. An hour plus the run.

## 16 — Existing Patterns move across, and free noticing becomes unmatched Patterns (2026-11-25)

### A push-back on a confirmed old Pattern is no longer recorded

- **Settled (25 Nov 2026, issue 24):** the confirmed and closed Patterns kept before the catalog were deleted, so this can't happen any more.

- **Kind:** risk
- **What:** a confirmed Pattern kept before the Pattern Catalog can still be offered with the Read (`read_pattern_offered` in `core/reply_plan.py`), but the keeping step no longer reads how the User took it (`plan_pattern_changes` in `core/patterns.py`). `last_offered_at` and `last_reaction` stay as they were.
- **Impact:** the live User can reject a Pattern they once agreed with and Zeph keeps using and offering it, with no wait. The Reply Plan keeps reading "they agreed".
- **Suggested fix:** in issue 09 (contested), read the reaction to an offered confirmed Pattern in code's terms and make it contested. Until then, a small option is to stop offering old confirmed Patterns. An hour either way.

### The ready gate doesn't know a User already agreed with a matched Pattern

- **Settled (25 Nov 2026, issue 24):** no agreed Pattern from before the catalog is left, so there is nothing to share twice.

- **Kind:** potential failure
- **What:** a match is a link (`patterns.matched_pattern_type_id`); the old confirmed Pattern and the Pattern of that Pattern Type are two rows. Nothing yet reads the link.
- **Impact:** once sharing is built, Zeph could share as new a Pattern the User agreed with months ago.
- **Suggested fix:** in issue 07, make "the User has a confirmed Pattern matched to this Pattern Type" an input to the gate (block, or share as "you've seen this before"). Small, inside that issue.

### Old evidence past Message Retention can't become Observations

- **Kind:** risk
- **What:** tagging again needs the User's exact words, so only Conversations whose messages are still kept (30 days) are tagged (`PatternMatcher._tag_again`). The command reports these as "evidence days with no messages left".
- **Impact:** most of the live User's older evidence gives no Observations when their Patterns are matched; those Patterns of Pattern Types start from what they say from now on.
- **Suggested fix:** run `make match-patterns` on production soon after Pattern noticing is on and the User has pressed "Got it", while more messages are still kept. No code.

### A Pattern keeps its first match

- **Kind:** risk
- **What:** `list_not_matched` leaves out any Pattern that has a link, so one matched to a Pattern Type is never checked against a better one added later.
- **Impact:** an old Pattern can stay linked to a near fit after its true Pattern Type is written.
- **Suggested fix:** let `make match-patterns TYPES=…` also look at Patterns already matched, and keep the new link only when the model picks the new Pattern Type over the old. A few hours, with a test.

### An unreadable matching answer is reported as "fits no Pattern Type"

- **Kind:** bug
- **What:** `PatternMatcher._ask` returns None both when the model says none and when two answers in a row can't be read; the report prints the same line for both (a warning goes to the backend log).
- **Impact:** an Admin can't tell a model failure from a real "no fit". The Pattern is asked about again on the next run, so nothing is lost.
- **Suggested fix:** carry "couldn't be read" in `PatternMatch` and print it. Under an hour.

### The unmatched review groups opposites together, and misses loose paraphrases

- **Kind:** risk
- **What:** entries are grouped by one closeness bar on the bge-small embedder (`unmatched_grouping_closeness_percent`, 80). Measured 25 Nov 2026: the same way in other words scores about 74 to 88, a different way up to about 78, and opposites about 91 ("Makes jokes when things get serious" and "Stops joking when things get serious").
- **Impact:** an entry can hold Users showing the opposite way, and one way of acting can be listed twice. The User count of an entry is a rough number.
- **Suggested fix:** if it shows up in real use, let the keeping model pick the entry (it is shown the existing descriptions, which hold no User details) instead of the embedder. Half a day, with a test.

### An entry with one User can point at that User

- **Kind:** risk
- **What:** the review page lists entries from one User up. The Users page shows how many unmatched Patterns each User has.
- **Impact:** with few Users (one live today), an Admin can tell who an entry is about, even though it holds no name or quote.
- **Suggested fix:** list an entry only from an Admin-set number of Users (2 or 3). An hour. Left out because the issue asks for every entry with its count.

### The code check on a general description can't catch every detail

- **Kind:** risk
- **What:** code drops a description with a digit, a quote mark, a capital after the first word or the User's name (`read_general_description`). A job or place written in lower case ("works at a bank near the river") passes; the prompt is what keeps those out.
- **Impact:** a detail about a User could reach the Admin page if the model ignores its prompt.
- **Suggested fix:** add general-description cases to the Pattern keeping Eval, or a small model check before a description is kept. Evals cost money, so the owner decides.

### A dropped entry is judged only by its User count

- **Kind:** risk
- **What:** a dropped entry comes back when its count is above the count when it was dropped (`shown_mark`). If two Users leave and two others arrive, the count is the same and it stays dropped; if it came back and a Pattern is then matched, it reads as dropped again.
- **Impact:** small: an entry may come back a little late.
- **Suggested fix:** store which Users had it when dropped. Not done: it would put User IDs on entries, which hold none today.

### Design files changed by the agent again

- **Kind:** note
- **What:** as issues 05, 10 and 14 did, issue 17 added a reference (`AdminUnmatchedPatterns.html`), its baseline, lines in `routes.json` and `manifest.json`, and the menu link on the other 13 admin references, though `web/design/README.md` says only the owner edits these. The page also puts the table template's filter pills above a card list. No other baseline changed.
- **Impact:** none seen; the owner may want to look at the new reference.
- **Suggested fix:** review `web/design/reference/AdminUnmatchedPatterns.html`, and say in the design README whether agents may add references when an issue asks.

## Comments`, in issue order, with one entry per finding:

```markdown
## NN — <issue title> (<YYYY-MM-DD>)

### <short title>

- **Kind:** bug | failure | risk | potential failure
- **What:** one or two sentences, with evidence (file:line, commit, Eval Run, output).
- **Impact:** what goes wrong, and for whom.
- **Suggested fix:** one concrete action, and roughly what it costs.
```

If there is nothing, the section holds one line: "Nothing found."

## 01 — Needs say how Curiosities are treated (2026-11-24)

### A never-Need still shows the Reply Plan the due Curiosities

- **Kind:** risk
- **What:** the Reply Plan picks the Need and the Curiosity in the same model call, so the due Curiosities can't be hidden under a Need set to never. Code drops any pick afterwards (`core/curiosities.py:243`, `settle_curiosities` in `core/reply_plan.py:859`) and logs 0 offered.
- **Impact:** the model can still shape its Moves around a Curiosity that code then drops, so the reply may lean toward a topic the Need says not to raise.
- **Suggested fix:** pick the Need first, then offer Curiosities in a second step only when the Need allows them. One more small model call per reply, and a reload of `reply_plan_prompt`.

### A never-Need doesn't stop questions the reply makes up itself

- **Kind:** potential failure
- **What:** in the Eval Run for issue 01 (Understanding, case `curiosity-raised-once`), Variant B had "Just chatting" set to never: 0 Curiosities offered, yet the reply still asked about the presentation, from its memory of the week.
- **Impact:** an Admin who sets a Need to never expects no such questions (for example under "Be heard"), but the User can still get one.
- **Suggested fix:** under a never-Need, tell the Reply not to bring up open topics from memory unless the User does. A small prompt change and an S$0.01 Eval run to check it.

### Needs and Moves page hints name the wrong step

- **Kind:** bug
- **What:** the hints say "when the Understanding picks this Need" (`web/src/components/NeedFields.tsx:69`) and "this Move" (`web/src/components/MoveFields.tsx:56`). The Reply Plan picks both.
- **Impact:** Admins get a wrong picture of which step and prompt to tune.
- **Suggested fix:** change both hints to "the Reply Plan" and update the matching design reference text. A few minutes.

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

## 03 — Users set how direct Zeph is with its Read (2026-11-24)

### The Reply model doesn't reliably call change_directness

- **Kind:** failure
- **What:** across three Settings Eval runs, `more-direct` passed 1 of 3 and `gentler` passed 1 of 2 (Eval Runs 2eb36fca, 11e0451e, 29a300a8). When it failed, the reply asked a question, or said "Done — I've set myself to direct" without calling the tool. In a live `/run`, "could you go easier on me…" got "you're on gentle now" while the setting was still direct. A plainer "please change how direct you are to gentle" did call it. Every other Settings case passes. Adding "Never say you changed a setting without calling its tool" to `reply_settings_instructions` helped `more-direct` once, but didn't fix it.
- **Impact:** a User asks Zeph to be gentler or blunter, is told it's done, and nothing changes. Their Dashboard still shows the old level.
- **Suggested fix:** try the Reply with thinking on, or a stronger reply model, for replies that offer settings tools. Compare on the two cases, 3 tries each, about S$0.05.

### A tool call sent to the User as plain text

- **Kind:** bug
- **What:** in Eval Run 2eb36fca (`more-direct`), deepseek-flash wrote the tool call into its reply instead of calling it. The made-up User got the messages "<tool call>" and "<function=change_directness>\n<parameter=directness>direct</parameter>\n</function>\n</tool_call>".
- **Impact:** real Users can get raw markup in chat, and the change they asked for isn't made.
- **Suggested fix:** in the chat model adapter, catch replies that hold `<tool call>` or `<function=` markup. Run the tool from them, or retry the call once, and never send that markup. A small adapter change with a test.

### Pixel test can't run as shipped

- **Kind:** failure
- **What:** `web/design/compare.cjs` waits for `networkidle`, which Clerk's `protect.clerk.com` probes never reach, so every signed-in page times out. This check used a copy in the git-ignored `web/design/.diff/` that aborts those requests. `M-Account` passes at 0.45% (limit 0.5%). The differing pixels are in the time zone field, the sticker icons and the "Delete my data" text, none of which this issue touched.
- **Impact:** every UI issue has to patch the test by hand to get a PASS. One small change to the Account page will push `M-Account` over the limit for reasons unrelated to that change.
- **Suggested fix:** the owner adds the `protect.clerk.com` abort to `compare.cjs` and looks at why those three parts of `M-Account` drift.

### Migration 0086 overwrites Admin prompt edits too

- **Kind:** risk
- **What:** like 0073 to 0081 (see 02), 0086 drops the stored `reply_plan_prompt` and `reply_settings_instructions` so they reload from the seed.
- **Impact:** the same as in 02: Admin edits to these two prompts are lost on deploy.
- **Suggested fix:** the same as in 02.

## 11 — Tagging step keeps Observations (2026-11-24)

### Tag names written out by hand in several places

- **Kind:** potential failure
- **What:** the tag values (relationship, power, setting, stance) are written out by hand in the enums in `core/models.py`, the reader in `core/observations.py:247` and `:475`, the tagging prompt (`seed/platform_settings.yaml:1298`) and the catalog loader (`adapters/pattern_catalog.py`).
- **Impact:** if the prompt and the code drift apart, the code checks will quietly drop the model's tags. Observations then lose their tags, or are dropped, with nothing to say why.
- **Suggested fix:** build the prompt's tag lists from the enums, so the code is the only place they are written. A small change, but it needs a reload of the tagging prompt.

## 13 — "Things you said that Zeph kept" (2026-11-24)

### Seed Copy is behind the design references, so Memories pixel tests fail

- **Kind:** failure
- **What:** `src/companion/seed/copy.yaml` still has "Conversation Summaries" (`memories.tabs.summaries` and the Day Summaries heading and intro) and an older Memories hero line ("short summaries of past Conversations"), while every `Memories*` reference says "Day Summaries" / "a short account of each day you talked". In fixture mode `compare.cjs` fails Memories--tab-summaries (0.71%), M-Memories (0.91%) and M-Memories--tab-patterns (0.58%) on main, and M-Memories--tab-quotes (0.64%) on this branch, all from that text.
- **Impact:** the pixel test can't pass for those pages, so real drift on them would go unnoticed; new Users get the old wording seeded.
- **Suggested fix:** update those seed texts to the references' wording (and a migration only if the live stored slots should change too); about half an hour.

### Tagging needs Users to be told first, so Evals of tagging keep nothing

- **Kind:** potential failure
- **What:** `PatternTagger.tag_from` (`core/observations.py`) now keeps nothing until `users.pattern_noticing_told_at` is set. Eval Users made by `adapters/evals/in_process_companion.py` never press "Got it".
- **Impact:** the tagging Eval (issue 14) and the whole-pipeline Eval (19) would see no Observations and score as if the tagger found nothing.
- **Suggested fix:** set `pattern_noticing_told_at` when the in-process companion makes its Eval User, as it already does for `ai_notice_acknowledged_at`; a few lines.

### A deleted quote could come back if a Conversation is ever tagged twice

- **Kind:** risk
- **What:** the User lock covers scoring and deleting a quote, but tagging's `observations.add_many` runs outside it. Today each Conversation is tagged once, so nothing deleted can be inserted again.
- **Impact:** if Conversation ends are ever retried after tagging, or old Conversations are tagged again (e.g. when a Pattern Type is added), a quote the User deleted could be kept again.
- **Suggested fix:** before building any retagging, keep a record of deleted quotes (Conversation and quote) and skip them in `plan_observations`; about an hour.

## 14 — Tagging Eval (2026-11-24)

### Owner corrects the drafted Tagging cases

- **Kind:** risk
- **What:** The 44 Tagging cases in `src/companion/seed/evals/cases/tagging.yaml` were drafted by Claude and are the defaults until the whole PRD is built (owner's decision, 24 Nov 2026; moved here from issue 14's last criterion).
- **Impact:** Until corrected, a Tagging Eval score measures the step against Claude's labels, not the owner's.
- **Suggested fix:** Follow `docs/pattern-evals/adding-tagging-cases.md`: correct on the Dashboard, run, then have an agent copy the cases into the seed.
- [ ] Owner corrected the Tagging cases

### Tagging context lines call the User "she"

- **Fixed (24 Nov 2026):** issue 22 (`archive/22-context-lines-gender-the-user.md`).

- **Kind:** bug
- **What:** In the first Tagging Eval run (run `4352910b`, case `conf-mum-holiday-plans`) the real tagging step wrote context lines like "she spent the evening resentful" and "Explaining why she gave in". The tagging prompt doesn't ask for they/them.
- **Impact:** Context lines are shown to Users as "Zeph's note" on "Things you said that Zeph kept" (issue 13), so a User can be misgendered on their own Memories page.
- **Suggested fix:** Add one line to `pattern_tagging_prompt`: write context lines with "they/them" (or "you") and never guess a gender; add a Tagging Eval rule or a code check later. Minutes; then re-run the Tagging Eval (about S$0.15).

### First Tagging Eval run: 33 of 44 pass

- **Kind:** failure
- **What:** Run `4352910b` (24 Nov 2026, live settings, `deepseek-flash` with thinking, S$0.1476): all four "anyone would" CONF.AVOID.BELONG cases (waiter, taxi, CEO, airline queue) kept nothing; the mum case was kept as situational (code marks a parent tagged power "above" as "anyone would"); three of four unclear cases came back as one clear Observation or two separate ones instead of one unclear; CTRL "real crisis" cases were tagged "for" or nothing instead of "against" (D2). Two seed cases were wrong for code's rules and were fixed in review (`conf-against-only-with-boss`, `unclear-conf-or-ach-boss-feedback` now expect situational).
- **Impact:** Until fixed, low-stakes stranger moments are never recorded as "anyone would" (so they don't count against a Pattern), parents count as "anyone would", and look-alike Pattern Types are rarely marked unclear, so scores lean on guesses.
- **Suggested fix:** The owner corrects the drafted cases first (issue 14's open criterion), then decide per finding: say in the tagging prompt when to tag "anyone would" moments and when to write one unclear Observation; consider narrowing CONF.AVOID.BELONG's `anyone_would_when` power `above` to people outside family (new catalog version). An hour plus a S$0.15 re-run.

### The estimate for never-run Tagging cases is off

- **Kind:** risk
- **What:** New run estimated 308,000 in / 39,600 out tokens (S$0.178) for 44 Tagging cases; the run used 79,120 in / 76,318 out (S$0.148). A never-run case uses a rough per-Eval figure (`ROUGH_TOKENS_PER_CASE`, 7,000 / 900) priced on the reply model, while tagging with thinking writes far more than it reads.
- **Impact:** Small here, but a new Eval or a Variant with a dearer model can be estimated well under its real cost. After one run the estimate uses each case's real tokens, so it corrects itself.
- **Suggested fix:** Set Tagging's rough figure to about 1,900 / 1,800 and price rough figures on the model of the step each Eval runs. Under an hour.

### An unclear case matches any pair holding the expected Pattern Type

- **Kind:** potential failure
- **What:** `matches` in `core/evals/tagging_eval.py` passes an unclear expectation when the expected Pattern Type is either of the two kept, whatever the other is (a CONF/ACH case passes if CONF/CTRL is kept).
- **Impact:** A Tagging case can pass with the wrong look-alike pair.
- **Suggested fix:** If the owner wants the pair checked, add an optional "second Pattern Type" field to the expected Observation. An hour.

### `make restart` web build failed once, then passed

- **Kind:** potential failure
- **What:** In the pattern-14 worktree the first `make restart` failed in `pnpm build` ("Build failed because of webpack errors"); the next two passed with no change. The error lines weren't kept.
- **Impact:** A deploy built on the server could fail the same way now and then.
- **Suggested fix:** If it happens again, keep the full build log and look for a memory or race cause.

### The first 44 Tagging cases were written for a three-type catalog

- **Kind:** eval quality
- **What:** Issue 15 grew the catalog from three Pattern Types to fifteen. The first 44 Tagging cases expect only CONF.AVOID.BELONG, ACH.WORTH.PERF or CTRL.UNCERT.PLAN; several now also fit a new look-alike (e.g. `conf-yes-to-sister-then-resents` could read as APPR.GIVE.NEEDED). The 24 new cases (one for, one against per new type) haven't been run.
- **Impact:** A Tagging run may now fail cases where the model picks a fair new look-alike, and each run costs several times more (the whole catalog goes in every call).
- **Suggested fix:** Run the Tagging Eval once (show the estimate first), then correct expectations to "unclear" with the right pair where the new types fit. An hour plus the run.

## 16 — Existing Patterns move across, and free noticing becomes unmatched Patterns (2026-11-25)

### A push-back on a confirmed old Pattern is no longer recorded

- **Settled (25 Nov 2026, issue 24):** the confirmed and closed Patterns kept before the catalog were deleted, so this can't happen any more.

- **Kind:** risk
- **What:** a confirmed Pattern kept before the Pattern Catalog can still be offered with the Read (`read_pattern_offered` in `core/reply_plan.py`), but the keeping step no longer reads how the User took it (`plan_pattern_changes` in `core/patterns.py`). `last_offered_at` and `last_reaction` stay as they were.
- **Impact:** the live User can reject a Pattern they once agreed with and Zeph keeps using and offering it, with no wait. The Reply Plan keeps reading "they agreed".
- **Suggested fix:** in issue 09 (contested), read the reaction to an offered confirmed Pattern in code's terms and make it contested. Until then, a small option is to stop offering old confirmed Patterns. An hour either way.

### The ready gate doesn't know a User already agreed with a matched Pattern

- **Settled (25 Nov 2026, issue 24):** no agreed Pattern from before the catalog is left, so there is nothing to share twice.

- **Kind:** potential failure
- **What:** a match is a link (`patterns.matched_pattern_type_id`); the old confirmed Pattern and the Pattern of that Pattern Type are two rows. Nothing yet reads the link.
- **Impact:** once sharing is built, Zeph could share as new a Pattern the User agreed with months ago.
- **Suggested fix:** in issue 07, make "the User has a confirmed Pattern matched to this Pattern Type" an input to the gate (block, or share as "you've seen this before"). Small, inside that issue.

### Old evidence past Message Retention can't become Observations

- **Kind:** risk
- **What:** tagging again needs the User's exact words, so only Conversations whose messages are still kept (30 days) are tagged (`PatternMatcher._tag_again`). The command reports these as "evidence days with no messages left".
- **Impact:** most of the live User's older evidence gives no Observations when their Patterns are matched; those Patterns of Pattern Types start from what they say from now on.
- **Suggested fix:** run `make match-patterns` on production soon after Pattern noticing is on and the User has pressed "Got it", while more messages are still kept. No code.

### A Pattern keeps its first match

- **Kind:** risk
- **What:** `list_not_matched` leaves out any Pattern that has a link, so one matched to a Pattern Type is never checked against a better one added later.
- **Impact:** an old Pattern can stay linked to a near fit after its true Pattern Type is written.
- **Suggested fix:** let `make match-patterns TYPES=…` also look at Patterns already matched, and keep the new link only when the model picks the new Pattern Type over the old. A few hours, with a test.

### An unreadable matching answer is reported as "fits no Pattern Type"

- **Kind:** bug
- **What:** `PatternMatcher._ask` returns None both when the model says none and when two answers in a row can't be read; the report prints the same line for both (a warning goes to the backend log).
- **Impact:** an Admin can't tell a model failure from a real "no fit". The Pattern is asked about again on the next run, so nothing is lost.
- **Suggested fix:** carry "couldn't be read" in `PatternMatch` and print it. Under an hour.

### The unmatched review groups opposites together, and misses loose paraphrases

- **Kind:** risk
- **What:** entries are grouped by one closeness bar on the bge-small embedder (`unmatched_grouping_closeness_percent`, 80). Measured 25 Nov 2026: the same way in other words scores about 74 to 88, a different way up to about 78, and opposites about 91 ("Makes jokes when things get serious" and "Stops joking when things get serious").
- **Impact:** an entry can hold Users showing the opposite way, and one way of acting can be listed twice. The User count of an entry is a rough number.
- **Suggested fix:** if it shows up in real use, let the keeping model pick the entry (it is shown the existing descriptions, which hold no User details) instead of the embedder. Half a day, with a test.

### An entry with one User can point at that User

- **Kind:** risk
- **What:** the review page lists entries from one User up. The Users page shows how many unmatched Patterns each User has.
- **Impact:** with few Users (one live today), an Admin can tell who an entry is about, even though it holds no name or quote.
- **Suggested fix:** list an entry only from an Admin-set number of Users (2 or 3). An hour. Left out because the issue asks for every entry with its count.

### The code check on a general description can't catch every detail

- **Kind:** risk
- **What:** code drops a description with a digit, a quote mark, a capital after the first word or the User's name (`read_general_description`). A job or place written in lower case ("works at a bank near the river") passes; the prompt is what keeps those out.
- **Impact:** a detail about a User could reach the Admin page if the model ignores its prompt.
- **Suggested fix:** add general-description cases to the Pattern keeping Eval, or a small model check before a description is kept. Evals cost money, so the owner decides.

### A dropped entry is judged only by its User count

- **Kind:** risk
- **What:** a dropped entry comes back when its count is above the count when it was dropped (`shown_mark`). If two Users leave and two others arrive, the count is the same and it stays dropped; if it came back and a Pattern is then matched, it reads as dropped again.
- **Impact:** small: an entry may come back a little late.
- **Suggested fix:** store which Users had it when dropped. Not done: it would put User IDs on entries, which hold none today.

### Design files changed by the agent again

- **Kind:** note
- **What:** as issues 05, 10 and 14 did, issue 17 added a reference (`AdminUnmatchedPatterns.html`), its baseline, lines in `routes.json` and `manifest.json`, and the menu link on the other 13 admin references, though `web/design/README.md` says only the owner edits these. The page also puts the table template's filter pills above a card list. No other baseline changed.
- **Impact:** none seen; the owner may want to look at the new reference.
- **Suggested fix:** review `web/design/reference/AdminUnmatchedPatterns.html`, and say in the design README whether agents may add references when an issue asks.

## 07 — Ready gate (2026-11-25)

### The first ruled-out topics list is a guess

- **Kind:** risk
- **What:** `pattern_ruled_out_topics` starts as abuse, sexual trauma, self-harm or suicide, eating and body image (`seed/platform_settings.yaml`). Decision 16 names no list. A topic added later doesn't reach Observations already tagged.
- **Impact:** a Pattern could rest on a painful topic Zeph asked about that isn't on the list yet.
- **Suggested fix:** the owner corrects the list on Platform settings before Pattern sharing is switched on for anyone.

### Scoring counts evidence against that only narrows a Pattern

- **Kind:** potential failure
- **What:** the gate leaves narrowing evidence out (`narrows` in `core/ready_gate.py`), but `PatternScorer` still counts it, so a strong "not with my partner" can pull a Pattern under the suspected bar, where the gate never looks.
- **Impact:** a true, narrow Pattern may never become ready.
- **Suggested fix:** work out the narrowing in scoring too, or have scoring ask the gate's rule.

### The Tagging Eval doesn't cover exclusions or ruled-out topics

- **Kind:** risk
- **What:** the tagging prompt now also flags exclusions and ruled-out topics; none of the 68 cases in `seed/evals/cases/tagging.yaml` checks them, and no Eval was run after the prompt change. In the first running-app check the real model flagged Grief but wrote no Observation at all for that Conversation; the prompt was then changed to say to keep noting them, and the second check kept two.
- **Impact:** tagging quality may have shifted without anyone seeing it; a missed exclusion lets a Pattern be drawn from a hard time.
- **Suggested fix:** run the Tagging Eval once (it costs money), and add cases for grief, a job loss and a ruled-out topic raised by Zeph and by the User.

### A ready Pattern can be stale between two looks

- **Kind:** risk
- **What:** ready is judged at Conversation end and when Observations are deleted. A Safeguard Event in the middle of a Conversation, or evidence fading, leaves it ready until the next look.
- **Impact:** once sharing exists, a Pattern could be shared right after a crisis.
- **Suggested fix:** issue 08 looks again before sharing (noted on issue 08).

## 08 — Sharing a ready Pattern (2026-11-25)

### Asked for a pattern, the Read says one that code never offered

- **Kind:** risk, needs the owner's decision
- **What:** in the running app, with the Pattern only suspected and nothing offered by code, "what patterns do you see in me? tell me one" got: "One, plainly: the yes comes out before you've checked whether you want to give it", with Mei, Dana, Tom and Priya as examples. The Reply Plan built it as its Read from the Life Threads in mind and the Agenda (which shows the Pattern Type's name and if / then, marked never to say). The Pattern's approved wording, quotes and Prediction never reached the reply, and nothing was recorded as shared. A line was added to `reply_plan_prompt` ("a Read is about this situation, not about who they are: never call it a pattern"); it softened the wording in other replies but not when the User asks outright.
- **Impact:** the gate holds for what code offers, but a User who asks gets much the same claim untested, with no Prediction and no record. This is where "the Read stays free" (decision 6) meets "code gates what it claims".
- **Suggested fix:** decide which wins when they ask. Options: leave it (the Read is free); have code tell the Reply Plan, when a suspected or contested Pattern is close to what the Read says, to say it is still getting to know them; or stop showing the Agenda's if / then to the Reply Plan. Then add an Understanding Eval case for it.

### The quotes a share used aren't stored, and a share can have no Prediction

- **Kind:** limit
- **What:** only the Prediction, as the check after the reply read it, is kept (`predictions`). Which quotes the reply used isn't kept, and a reply the check finds told the Pattern but gave no Prediction is still shared, with no Prediction row.
- **Impact:** the Patterns tab (issue 18) can show all a Pattern's quotes but not which were said; issue 09 must cope with a shared Pattern that has no Prediction (make one).
- **Suggested fix:** handle both in issues 09 and 18 (noted on them).

### Agreement is kept and valued, but nothing reads a shared Pattern's score yet

- **Kind:** limit
- **What:** agreeing is kept as a reaction worth one weak sign for (`reaction_points`), and pushing back as one against. The only place that adds reactions to a score today is the logged score of the move to contested. Scoring never moves a shared Pattern, so the weak sign changes nothing a User or Admin sees until issue 09 confirms or closes shared Patterns.
- **Impact:** none yet; issue 09 must add reactions when it reads a shared Pattern's score.
- **Suggested fix:** noted on issue 09.

### The check after the reply can fail after the Pattern was told

- **Kind:** risk
- **What:** the check runs once the reply is sent. If the call fails, or the reply was only partly sent, the Pattern stays ready and isn't counted, though the User may have read it. It can then be told again.
- **Impact:** a rare double telling.
- **Suggested fix:** if it shows up in real use, run the check before sending, as the Woven-in Check-in does (it costs a few seconds per sharing reply).

### "It shows with colleague, family, friend" reads stiffly

- **Kind:** polish
- **What:** where a Pattern shows is given to the models as the raw tag values. The replies turned it into good prose ("the people closest to you get the real thing").
- **Suggested fix:** leave unless replies start echoing it.

### Migration 0100 reloads three prompts

- **Kind:** note
- **What:** `pattern_tagging_prompt`, `reply_plan_prompt` and `reply_settings_instructions` reload from the seed on deploy, so an Admin's edits to them are lost.

### Design files changed by the agent again

- **Kind:** note
- **What:** `web/design/reference/Account.html` and `M-Account.html` gained the "Keep noticing after I disagree" card (a copy of the photo switch card with new words), and their two baselines were rebuilt on this machine. Fixture Alex has Pattern sharing working so the card is drawn. The words are drafts for the owner to correct under Copy.

### The pixel test still can't run as shipped

- **Kind:** bug, already known
- **What:** `compare.cjs` hangs on Clerk's probe requests; a copy that blocks them was used and deleted. With it, `AdminModelCallTrace` and `AdminCheckInKinds` fail on page height only (0.02% and 0.08% of pixels differ), as noted before this work.

## 09 — Prediction follow-up and confirming (2026-11-25)

### One story can count twice: as a Prediction outcome and as an Observation

- **Kind:** risk
- **What:** in the running app, "Dana changed the plan and I told her straight away I wasn't ok with it" was read as the Prediction's outcome (didn't, one strong sign against) and also tagged as an Observation against the Pattern (another strong sign). The score dropped by about 280 for one event. The same happens for a story that makes a Prediction come true and is tagged as an Observation for.
- **Impact:** a shared Pattern moves about twice as fast as the numbers suggest, both ways. With the bar for "strong evidence after sharing" at 300, two such stories are close to confirming with one Prediction.
- **Suggested fix:** decide which should count. Simplest: when a Conversation settles a Prediction, don't count that Conversation's Observations of the same Pattern Type toward "after sharing", or halve them.

### The Reply Plan often picks another Curiosity, and a reply may not ask the one picked

- **Kind:** finding
- **What:** code puts the Prediction Curiosity first, but the model picks. In the run it twice chose a guess or a next Move instead, and once it picked the offer of a new Prediction but the reply was only a greeting; the check rightly kept nothing. A picked Curiosity counts as asked whether or not the reply asked it (true of every Curiosity). For a follow-up that means it is not asked again in that window, and the Prediction is dropped at its last day if the User doesn't bring it up.
- **Impact:** some Predictions will go unanswered. Brush-offs of other Curiosities also slow it down (the pace doubles for 3 days after 2 in a row).
- **Suggested fix:** watch it in real use. If it matters, check after the reply whether the follow-up was asked (as the Woven-in Check-in does) and leave it waiting if not.

### A new Prediction is much the same as the last

- **Kind:** limit
- **What:** a Pattern Type has one `prediction_wording`. After the first came true, the new one Zeph gave was the same thing in other words ("next time Mei asks… just notice whether you've said yes before you decided").
- **Impact:** "two Predictions came true" is really the same Prediction twice.
- **Suggested fix:** give each Pattern Type two or three Prediction wordings and have code pick one not used yet. Catalog work for the owner.

### With the starting numbers a shared Pattern can hardly be closed

- **Kind:** note
- **What:** a Pattern is ready at 300 points or more and closes under −150. One Prediction that didn't is −140. It would take several failed Predictions and evidence against before it closes, and "didn't" Predictions don't stop it being confirmed by two that came true.
- **Suggested fix:** the owner may want a second rule, such as "closed when more Predictions didn't than did, after N".

### "Strong evidence after sharing" is a number I chose

- **Kind:** decision for the owner
- **What:** the issue says "strong evidence after sharing" confirms, with no number. I added `pattern_confirm_points_after_sharing`, starting at 300 (the ready bar): the Observations said on a later day than the share must reach it by themselves. Reactions and Prediction outcomes don't count toward it.
- **Suggested fix:** confirm or change the number on Platform settings.

### What happens to a Prediction nobody answers

- **Kind:** decision for the owner
- **What:** the issue says a follow-up not asked in time is closed. I also mark its Prediction "not followed up" (it counts nothing) and Zeph then offers a new one. One asked and never answered ends the same way. If the User asks Zeph to drop it, the Prediction is dropped and Zeph never raises that Pattern's Predictions again; the Pattern stays shared.

### The floor is checked before the Predictions

- **Kind:** note
- **What:** a shared Pattern under the floor is closed even if two Predictions came true in the same Conversation end.

### Confirmed Patterns reach only the Portrait

- **Kind:** limit
- **What:** a confirmed Pattern is in the Portrait's input (under the old heading "Patterns they agreed with") and counts for Familiarity. The Reply Plan is still not shown shared or confirmed Patterns, and a confirmed Pattern is never closed or moved again. The Patterns tab is issue 18.
- **Suggested fix:** a later issue: show the Reply Plan the confirmed Patterns, and rename the Portrait heading (that reloads `portrait_prompt`).

### Migration 0101 reloads the tagging prompt

- **Kind:** note
- **What:** `pattern_tagging_prompt` reloads from the seed on deploy, so an Admin's edits to it are lost. The friend testing loses nothing: no User data is changed.

### No Eval covers Prediction outcomes

- **Kind:** note
- **What:** the Tagging Eval hasn't seen the new `prediction_outcomes` part of the prompt, and none was run (Evals cost money).

## 18 — The Patterns tab shows the Patterns Zeph told the User (2026-11-25)

### Deleting a Pattern they disagreed with forgets the disagreement

- **Kind:** risk
- **What:** `UserMemoryService.delete_pattern` deletes the Pattern with its reactions and its own quotes. Nothing is kept to say the User rejected it (or that it didn't hold up).
- **Impact:** if they later say new things that fit it, Zeph can notice it again from the start and, in time, tell them a Pattern they already said no to.
- **Suggested fix:** the owner decides: either that is right ("delete means forget everything"), or keep a small "never again" mark per User and Pattern Type that the ready gate reads. About half a day.

### A told Pattern whose Pattern Type left the catalog can't be seen or deleted

- **Kind:** potential failure
- **What:** `told_patterns` (`core/told_patterns.py`) shows only Patterns whose Pattern Type is in the catalog now, as there is no approved wording otherwise.
- **Impact:** the User was told it, but can't see it or delete it from the tab; deleting all their data still removes it.
- **Suggested fix:** keep the wording used on the Pattern when it is shared, and show that. Small.

### The switch shows while Pattern sharing is off for them

- **Kind:** note
- **What:** "Keep noticing after I disagree" shows under "You disagreed" whenever they have such a Pattern; on Account & privacy it shows only while Pattern sharing works.
- **Impact:** none known; the two pages differ slightly.
- **Suggested fix:** owner's call; one line either way.

### Design files changed by the agent again

- **Kind:** note
- **What:** the Patterns panel in `Memories--tab-patterns.html` and `M-Memories--tab-patterns.html` was redrawn from existing parts, the empty-state words in `States.html` changed, and three baselines were rebuilt on this machine. All the tab's words are drafts for the owner to correct under Copy.

### The pixel test still can't run as shipped

- **Kind:** bug, already known
- **What:** `compare.cjs` hangs on Clerk's probe requests; a copy that blocks them was used and deleted. `Memories--tab-summaries` (0.75%), `M-Memories` (0.91%) and `M-Memories--tab-quotes` (0.64%) fail on main too.

## 19 — A whole-pipeline Eval (2026-11-25)

### A full run of the 5 cases stops at the starting token limit

- **Kind:** failure
- **What:** the Eval run token limit is 1,000,000. Real case runs used 284,000 (12 texts), 415,000 and 445,000 tokens (16 texts), so the 5 seeded cases need about 2,000,000 and the run stops between Conversations as Stopped over limit.
- **Impact:** the first full score against the 70% target can't be had until the limit is raised.
- **Suggested fix:** raise the limit on Admin → Evals → Model Prices to about 3,000,000 before a full run, or run single cases. A full run is about S$1.40 and over an hour.

### Three of the five cases have never been run

- **Kind:** risk
- **What:** only `ordinary-fortnight` and `folds-with-sister-and-friends` were run with the real model (the owner chose the smallest proof). The look-alike cases (`goes-quiet-and-says-fine`, `cannot-stand-waiting`, `never-arrives`) are untested drafts.
- **Impact:** nothing is known yet about look-alikes in the whole pipeline, or about the 70% target. A script may also simply not reach ready.
- **Suggested fix:** run them one at a time (about S$0.30 each) and correct the scripts.

### A case with nothing ready passes

- **Kind:** risk
- **What:** the issue's rule is "passes when every ready Pattern is one of the true ones", so a broken pipeline that makes nothing ready is all passes. A Conversation-end step that fails is also logged and skipped (`core/post_conversation.py`), so it shows only as fewer Patterns found.
- **Impact:** a green run can hide a dead pipeline.
- **Suggested fix:** read "true Patterns found" in the report; consider failing a run that finds none of its true Patterns.

### No Pattern was shared in any run

- **Kind:** risk
- **What:** in the real run the true Pattern was ready at the end and was never shared: the last Conversation's two texts didn't lead the Reply Plan to share it. The made-up User has Check-ins off and the script ends a day later, so sharing by Check-in is never reached.
- **Impact:** the "shared" half of the result has only been seen in tests of the result code, not in a real run.
- **Suggested fix:** add a case whose last Conversations invite it ("anything you've noticed about me?"), or one with Check-ins on and a week's wait.

### The scripted User never answers Zeph

- **Kind:** risk
- **What:** the texts are written into the case, so they don't answer Zeph's aimed Curiosities or Thought Experiments. The counter-test is met by a scripted "it doesn't happen with…" story.
- **Impact:** Explorations and the Agenda are run but not really tested here.
- **Suggested fix:** if that matters, add a model that plays the User from a hidden brief; it costs more and varies more.

### The result panel has no reference file

- **Kind:** risk
- **What:** `web/src/components/WholePipelinePatterns.tsx` reuses the parts of the Tagging result, but its words ("Became ready or shared", "Got as far as", "Stands now", "True Patterns missed", "Stopped by", "True", "Not true", "Missed") are in no `web/design/reference` file, and fixture mode has no sample for `/admin/evals/cases/whole_pipeline/new`. No design file was changed.
- **Impact:** no pixel test covers it; it was checked by eye at 1280 and 390.
- **Suggested fix:** the owner adds a reference (like `AdminEvalTaggingCase`) or approves the words.

### The Dashboard shows no share for the whole run

- **Kind:** risk
- **What:** only the terminal report prints "N of M ready Patterns true (X%, target 70%)". A Dashboard run shows each case's Patterns, so the share must be added up by hand.
- **Suggested fix:** add a line to the run page once a reference shows where.

### `make eval` no longer runs every Eval

- **Kind:** risk
- **What:** with no Eval named it leaves out Whole pipeline (`evals_run_by_default` in `core/evals/models.py`), because of its cost. Someone who expects "all Evals" gets nine of ten.
- **Suggested fix:** none needed if the owner agrees; `evals/README.md` says so.

## Comments
