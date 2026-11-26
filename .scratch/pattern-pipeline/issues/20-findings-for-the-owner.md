# 20 — Bugs, risks and failures found while building the pattern pipeline

Status: needs-triage
Track: shared
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 25, 26, 27, 28, 29, 30, 31, 32

## What this is

The final issue of the pattern-pipeline PRD (`.scratch/pattern-pipeline/PRD.md`). While agents work on the other issues of this PRD, they log here every bug, risk, failure or potential failure they find that their own diff doesn't fix. Once the other issues are done, the owner and an agent work through the list together.

Log only:

- **bug**: something that behaves wrongly today;
- **failure**: a check, test, Eval or tool that fails;
- **risk / potential failure**: something that works today but can go wrong for Users, data or cost.

Don't log notes about how your own work went.

## When you finish an issue of this PRD

Before archiving, ask: did I find a bug, failure, risk or potential failure, in my task or outside it, that my diff doesn't fix? Add one section for your issue above `## 44 — Narrowing and sharing use every Condition (2026-11-26)

### The Patterns tab has new Copy that no reference file draws

- **Kind:** risk
- **What:** a narrowing by audience, stakes, stance, setting or state is shown with a new line (`memories.patterns.shows_when`, "It shows in a group; not one-to-one.") and 25 value words (`memories.patterns.condition.*`). `web/design/reference/Memories--tab-patterns.html` draws only the relationship line, so the pixel test passes without seeing the new words. Relationship words are seeded as drawn ("friend", "colleague"), next to "your partner" and "strangers".
- **Impact:** the design rule "the reference changes first" wasn't met for these words, and a User can read "It shows with friend, colleague; not with your partner."
- **Suggested fix:** the owner rewords the slots on Admin → Copy and adds a non-people narrowing to the reference file, then rebuilds the baseline. Half an hour.

### A state gap on top hides every other gap when sharing

- **Kind:** risk
- **What:** `not_seen_yet` (`core/pattern_sharing.py`) takes the Agenda's one open missing-Condition need. When that is the state going in, the sharing reply is handed nothing, even if another Condition is one-sided too.
- **Impact:** a User whose stories all say they were worn out hears no "one thing I haven't seen".
- **Suggested fix:** let `missing_condition` skip state when asked for the sharing reply. A small change, plus a test.

### The unseen value is often a third value of the Condition that already narrows

- **Kind:** risk
- **What:** in the running-app check the Pattern was narrowed "in a group; not one-to-one", and the unseen value handed over was "with other people watching". The first reply turned this into "No idea how it goes when it's just you and one other person watching".
- **Impact:** the one thing Zeph says it hasn't seen can be the least useful one, and can read oddly next to the narrowing.
- **Suggested fix:** when sharing, pass over a Condition that already narrows the Pattern and take the next one-sided one. A small change to `not_seen_yet`, to be agreed since it bends "no second version of the rule".

### A told Pattern keeps its old narrowings

- **Kind:** risk
- **What:** narrowings are saved only when the ready gate judges a Pattern (`ReadyKeeper._look`). A shared, confirmed or contested Pattern keeps the ones it had, while its score is counted with today's rule and settings.
- **Impact:** the Patterns tab can show "It shows with …; not with …" for a narrowing the score no longer uses, for example one kept with one story before this issue.
- **Suggested fix:** save the narrowings again in `settle_shared` at each Conversation end. Small.

### Whether the reply said the unseen value is not checked or kept

- **Kind:** potential failure
- **What:** the unseen value is an instruction to the Reply. The small check after the reply reads only "shared" and the Prediction, and nothing is stored, so the Patterns tab and the trace page don't show it.
- **Impact:** a reply can skip it or say it as a claim and nothing notices; no Eval case covers it either.
- **Suggested fix:** add `not_seen_handed` to the Reply Plan's shape, and one Understanding Eval case with a Judge rule ("says one thing it doesn't know, as not known"). About S$0.02 a run.

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

## 25 — Eval cases for the Agenda (first real run, 25 Nov 2026)

Run `1641c640`, 12 cases once: 9 passed, 3 failed. 108,180 tokens in, 22,240 out, S$0.0754 (estimate S$0.0740). One case was then rewritten and run alone (`ee9f97a9`, pass, S$0.0057). Nothing was tuned: the prompts are issue 26's.

### The reply says the User's words back when it asks the aimed question

- **Kind:** to decide
- **What:** `agenda-unclear-story-asked`. The Reply Plan picked the aimed Curiosity and the reply asked it as one question, but it wrote "You said yes the moment she asked", close to the kept quote ("I said yes straight away"). The Judge failed `no_quote_back`, and also `never_names_a_pattern`, calling that line "a tendency".
- **Impact:** the User can feel their words are being kept and used as evidence. The second failure looks like the Judge's rule being too wide, not Zeph naming a Pattern.
- **Suggested fix:** in issue 26, look at how `describe_story` hands the story to the reply (it gives the context line, never the quote, so the model worked the words out itself). Tighten `never_names_a_pattern` so it is only about naming a habit, not about recalling an event.

### With two Explorations the Reply Plan asked neither

- **Kind:** to decide
- **What:** `agenda-two-explorations-top-one-asked`. Both aimed Curiosities were offered; the Reply Plan picked Just chatting with Get curious, brought up no Curiosity and gave no reason. The same kind of quiet-evening Message got the aimed Curiosity in three one-Exploration cases.
- **Impact:** one run, so it may be chance. It may also be that two "ask about a recent time at…" Curiosities fit a "nothing day" worse than a story does.
- **Suggested fix:** run it with Repeats before reading anything into it; the owner may want a Message that fits better.

### Aimed Curiosities are offered in the order written, not in the Agenda's order

- **Kind:** risk
- **What:** the Reply Plan is told "when an aimed Curiosity's day has come, it is first among the Curiosities above". With two Explorations there are two, listed by when they were saved (`list_waiting` orders by `position`), and `plan_agenda` writes them in the Explorations' stored order, not by rank. So number 1 can be for the lower-ranked Exploration. Seen in a test of the seed case, where the order changed between runs.
- **Impact:** the model has no sure way to tell which aimed Curiosity is for the top Exploration.
- **Suggested fix:** write, or offer, aimed Curiosities in rank order. A rule change, so it is for the owner (issue 26).

### The Safeguard took "dad's in hospital" as a crisis

- **Kind:** to decide
- **What:** the first draft of `agenda-not-asked-while-struggling` said "dad's in hospital, they think it's his heart. I can't stop shaking". The Safeguard answered with the helpline message, so the Understanding never ran. The case now uses losing a flat, which passes.
- **Impact:** a frightened User with a relative in hospital gets the crisis reply, not Zeph.
- **Suggested fix:** the owner decides whether that is wanted; if not, add it to the Safeguard Eval as a false alarm.

### Must-not-ask is decided by code before the model sees anything

- **Kind:** risk
- **What:** after a brush-off, a drop or a try yesterday, code has already taken the aimed Curiosity away. The four must-not-ask cases passed, but what they test is narrower than it sounds: that the reply doesn't go back to the story on its own while the Agenda is still shown. The guide says so.
- **Suggested fix:** none; a wrong-moment case where the Curiosity *is* offered (a hurried or practical Message) would test the model's own judgement. The owner may want one.

### The Tagging result's "Unclear stories" part has no reference file

- **Kind:** risk
- **What:** the owner agreed (25 Nov 2026) to a fourth part built from the Tagging result's own rows. Its words are new: "Unclear stories", "Ended clear", "Stayed unclear", "Was", "Asked about in this Conversation", "Now", "Expected", "Clear for …", "Unclear", and "N unclear story wrong" on the verdict pill. It shows only when a case has unclear stories, so `AdminEvalTaggingCase` is unchanged.
- **Impact:** no pixel test covers it; checked by eye at 1280 and 390.
- **Suggested fix:** the owner approves the words or adds them to the reference.

### A try's made-up Conversation is given replies so the pace allows the next Curiosity

- **Kind:** risk
- **What:** the pace between Curiosities counts replies since the last one was asked. A made-up try has none after it, so the next aimed Curiosity would never be offered on the case's first Message. Setup adds twice the Admin-set number of made-up replies after each try (`add_replies_after` in `core/evals/made_up_patterns.py`).
- **Impact:** the pace rule itself is not tested by these cases.
- **Suggested fix:** none needed; the tests of the pace cover it.

## 27 — Four reply-path faults a User can meet today (2026-11-25)

### Reply thinking on made the Reply call the settings tool every time

- **Kind:** risk
- **What:** in Eval Run 2a7a1577 (`more-direct` and `gentler`, 3 tries each) the Reply's first draft called `change_directness` 5 of 6 times on the live settings, 6 of 6 with `response_thinking` on, and 4 of 6 on deepseek-v4-pro. The code guard now catches the misses, at the price of a second Reply call.
- **Impact:** without thinking, about 1 settings request in 6 needs the reply written twice, so it is slower; a few may still end as the reply-failed message.
- **Suggested fix:** the owner decides whether to turn Reply thinking on (Prompts & models). It costs more and waits longer on every reply. A bigger run (5 repeats, about S$0.15) would say if 6 of 6 holds.

### A settings request can end as "my thoughts got tangled"

- **Kind:** potential failure
- **What:** when the reply is written twice and still says a setting changed with no tool called, nothing is sent but the reply-failed message. Seen 2 of 18 in Eval Run 2a7a1577. After the note to the model was made firmer: 0 of 6 in Eval Run eb03b46e and 0 of 5 forced live runs.
- **Impact:** the User is not lied to, but has to ask again.
- **Suggested fix:** if it shows up in the Model Call Log (two "Settings claim check" calls in one trace, then no reply), force the tool call on the second try (`tool_choice`), which needs a small change to the chat model port.

### One more model call on every reply

- **Kind:** risk
- **What:** the settings claim check runs before every reply that called no settings tool, which is nearly all of them (`SettingsTools._correction` in `core/chat_settings.py`). It is a small call on the Check-in model without thinking.
- **Impact:** each reply waits about a second longer and costs a little more. The load test's reply time goes up by one fake call.
- **Suggested fix:** watch the cost for a week. If it matters, run the check only when the Understanding says the User asked for a change, which means a new Understanding field and a prompt reload.

### The Reply still leaves out picked Curiosities, most of all Prediction follow-ups

- **Kind:** failure
- **What:** in the live run a Prediction follow-up picked under Just chatting was left out by the real Reply; it now stays waiting, but it was picked again on the next message and left out again. The follow-up's wording is a long instruction, not a question.
- **Impact:** nothing is lost any more, but a follow-up may be picked several times before it is asked, and each pick drops that reply's question Move.
- **Suggested fix:** count how often the asked check says no in the Model Call Log ("Curiosity asked: No" with one offered). If it is often, shorten the follow-up instruction or tell the Reply plainly it is a question to ask.

### Curiosity Check-ins are marked raised without the asked check

- **Kind:** potential failure
- **What:** a Curiosity sent as a Check-in on its own is marked raised when the Check-in is sent (`core/check_ins.py:1139`), whether or not its words asked it.
- **Impact:** the same loss issue 27 fixed for replies, on the Check-in path.
- **Suggested fix:** call the same check from the Check-in path; best done with issue 30.

### A rewritten reply can run a tool twice

- **Kind:** potential failure
- **What:** when the claim check has a reply written again, tools its first draft called (web search, sticker adding) run again in the second (`ResponseComposer.compose`). A picked sticker or photo is dropped, but a web search is paid twice and counts twice toward the daily limit.
- **Impact:** rare (a false settings claim and a search in one reply); a little cost.
- **Suggested fix:** leave it unless seen.

### The list of dropped topics has no limit

- **Kind:** risk
- **What:** every Curiosity a User ever asked to drop is shown to every Reply Plan and reply (`CuriosityRaiser.due`).
- **Impact:** for a User who drops many topics over months, each prompt grows.
- **Suggested fix:** cap it at the newest 20 if a real User gets near that.

### The Eval estimate was less than half the real cost

- **Kind:** failure
- **What:** the owner was shown about S$0.09 for 18 cases and S$0.014 for 6; they cost S$0.20 and S$0.05. The two cases had never run, so a rough figure was used, and the estimate for a Variant on a dearer model was low. Once the cases had run, the estimate for the same 6 cases read S$0.098, which was too high.
- **Impact:** the owner agrees to a run on a wrong number.
- **Suggested fix:** the same fix as "The estimate for never-run Tagging cases is off": a better rough figure per Eval, checked against real runs.

## 32 — Make the Whole-pipeline Eval a result we can trust (2026-11-25)

Closes four findings of section 19: "A case with nothing ready passes" (it now fails when the User has true Patterns), "Three of the five cases have never been run" (each ran), "No Pattern was shared in any run" (three were) and, for single-case runs, the token limit (each case is under it; a full run of the 6 cases still needs the limit at about 3,000,000). Runs and costs: `archive/32-whole-pipeline-eval-can-be-trusted.md`.

### One comparing line switches off narrowing

- **Kind:** failure
- **What:** in Eval Run cba7a37a the text "it didn't scare me at all, saying it. it's with mum, Rosa and people at work that I cave" was tagged as evidence against CONF.AVOID.BELONG with no relationship. `narrowings_of` (`core/ready_gate.py`) makes no narrowing when any clear evidence against has no person tag, so the "not with my husband" story counted fully against (over the 100-point bar) and the Pattern stopped at "counter-test" with all its evidence for in place.
- **Impact:** a real User who sums up "it's only with X that I do this" can block their own true Pattern. `folds-with-sister-and-friends` has the same kind of line and passed only because the tagging step read it differently that day.
- **Suggested fix:** decide whether evidence against with no person tag should be left out of narrowing instead of cancelling it, or whether the tagging prompt should tag such a line with the person it names. Not tuned here. The scripts now keep the counter-test story to one text.

### A parent is tagged "above", which for CONF.AVOID.BELONG is what anyone would do

- **Kind:** risk
- **What:** in Eval Run ba027a22 every story about the made-up User's mum was tagged power "above". CONF.AVOID.BELONG's `anyone_would_when` is `power: [above]` ("people in charge"), so those Observations were situational, counted for nothing, and the Pattern stopped at "situations" with two of three.
- **Impact:** folding with a parent is the most common form of this Pattern and may never count for a real User.
- **Suggested fix:** the owner decides whether "above" should mean a parent, or only a boss or official; then word it in the tagging prompt or the catalog. The script now uses a brother.

### An opinion scores too low to reach ready

- **Kind:** risk
- **What:** in Eval Run aa7520fb CTRL.UNCERT.PLAN had three situations and an answered counter-test and still stopped at "score": its strong sign ("waiting is worse than a no") was said as an opinion each time, and the "relaxed with Mia" story counted against in full because Mia had no relationship named. With the sign told as a story and "my girlfriend Mia", it became ready and was shared (61815c07).
- **Impact:** people often say how they feel in general, not as one story. Such a User may stay suspected.
- **Suggested fix:** none now; watch it on real Users. It is the Agenda's job to ask for a story.

### The reply told a Pattern that code never offered

- **Kind:** failure
- **What:** in Eval Run cba7a37a the Pattern was only suspected, so nothing was offered for sharing; asked "is there anything you've noticed about me?", the reply laid out the whole pattern anyway ("That's the pattern, as I see it"), with no Prediction and nothing recorded. The same as section 08, "Asked for a pattern, the Read says one that code never offered", now seen in a whole run.
- **Impact:** a User is told a Pattern the gate hadn't passed, and the Patterns tab shows nothing.
- **Suggested fix:** as in section 08. Not tuned here.

### One of two true look-alikes was missed

- **Kind:** risk
- **What:** in Eval Run 31ce319c (`goes-quiet-and-says-fine`) CONF.WITHDRAW.HURT became ready and APPR.HIDE.BURDEN stayed suspected, stopped by situations. The case passes, since one true Pattern was found.
- **Impact:** unknown from one run whether the script gives too little for the second or the tagging step folds the two together.
- **Suggested fix:** read the run's tagging calls before changing the script; Repeats would say if it is steady.

### A failed step is read from the log

- **Kind:** risk
- **What:** the Eval learns a Conversation-end step failed from what the app logs on its thread while the scheduled work runs (`adapters/evals/logged_failures.py`), since the steps log and skip. Anything else that logs an error in that work shows as "Conversation-end step failed" too, and a step that swallowed a failure without logging an error wouldn't show.
- **Impact:** the check is as good as the logging.
- **Suggested fix:** none needed now. If steps ever need to report failures to the live app too, have `PostConversationProcessor` return them.

### The rough estimate for a never-run Whole-pipeline case is low

- **Kind:** failure
- **What:** `make eval` showed S$0.28 for each never-run case; they cost S$0.29 to S$0.44. The owner was told about S$1.40 to S$1.50 for four runs and they cost S$1.49, but seven case runs were needed in all: S$2.63, plus S$0.04 for a small check.
- **Impact:** the same as section 27's estimate finding.
- **Suggested fix:** raise the rough figure in `core/evals/costs.py` to about 350,000 in and 160,000 out.

### An existing database keeps old seed cases unless a migration reloads them

- **Kind:** risk
- **What:** seed cases load only where the key isn't stored. Migration 0104 reloads `cannot-stand-waiting` where no Admin edited it; the new `asks-what-zeph-noticed` loads by itself.
- **Impact:** an edited copy on production keeps the old script, with no warning.
- **Suggested fix:** none needed unless the owner edited that case.

## 30, 35 to 39 — The owner's decisions before Pattern sharing is on (2026-11-25)

Settles from the sections above: 02 "Curiosity Check-ins ignore pace and backing off" (the owner chose to leave it), 07 the ruled-out topics and "Scoring counts evidence against that only narrows", 08 and 32 "the Read says a Pattern code never offered", 09 one story counting twice, the closing rule, the same Prediction twice, the unanswered Prediction and the 300, 13 "a deleted quote could come back" (it did: fixed), 18 both findings, 32 "One comparing line switches off narrowing".

### The owner corrects the 45 drafted Prediction wordings

- **Kind:** risk
- **What:** each Pattern Type now has three `prediction_wordings`, drafted by Claude (issue 38).
- **Impact:** a weak Prediction tests nothing, and two of them now confirm a Pattern.
- **Suggested fix:** follow "Writing and correcting Predictions" in `docs/pattern-catalog/README.md`.
- [ ] Owner corrected the Prediction wordings

### The gate when asked is not live on production until the Reply Plan prompt is merged

- **Kind:** risk
- **What:** migration 0109 keeps an Admin-edited `reply_plan_prompt`, and production's is edited. The new fields `asked_for_patterns` and `named_pattern` are only in the new seed text.
- **Impact:** on production a User who asks for their patterns still gets what they got before, and replies never name a told Pattern, until the new text is merged in.
- **Suggested fix:** after the deploy, merge the two new field descriptions and the two JSON lines into the stored prompt on Prompts & models (`docs/PROMPT_EDITS_AND_DEPLOYS_GUIDE.md`). Do it before Pattern sharing is switched on for anyone.

### Stronger models read something into the ask itself

- **Kind:** failure
- **What:** in Eval Run `898e711d`, asked "what patterns do you see in me?" by a User who had told no story, deepseek-v4-pro and claude-fable-5.2 declined to name a pattern but added a view of the asking ("you'd rather hear something true than something nice"); 1 of 3 passed each. Flash and claude-opus-5.5 passed 3 of 3. The fixed section now says to give no view when no situation was told; that wasn't run again.
- **Impact:** small: no Pattern is claimed, but the reply still says something about who they are.
- **Suggested fix:** if the reply model is changed, run `make eval CASES=asked-for-patterns-nothing-ready` with Repeats first. The Judge rule `says_no_pattern_when_asked` is a draft for the owner to correct.

### An Eval estimate doesn't price a Variant's dearer model

- **Kind:** failure
- **What:** the three-model run was estimated at S$0.07 and cost about S$1.2. The same finding as sections 14, 27 and 32.
- **Suggested fix:** price each Variant's rough figure on the models it overrides (`core/evals/costs.py`).

### A new Prediction's wording number is worked out twice

- **Kind:** potential failure
- **What:** the offer Curiosity is written with the next wording, and the number is worked out again when the reply that gave it is checked (`PredictionKeeper._check_and_record`). A catalog version that reorders the list in between would number it wrongly.
- **Impact:** rare; a Prediction could count as a different test than the one given.
- **Suggested fix:** keep the number on the offer Curiosity. Until then, never reorder `prediction_wordings` (the guide says so).

### The early follow-up is found through Life Threads only

- **Kind:** limit
- **What:** a follow-up is due early when a Life Thread in mind is one the Pattern showed in, or has a person in it that the Pattern's Observations are about. A person who is in no Life Thread doesn't bring it forward.
- **Suggested fix:** watch in real use.

### The stop after unanswered Predictions also lifts when Zeph names the Pattern

- **Kind:** limit
- **What:** offers start again when a reaction (agreed or pushed back) is read after the last unanswered Prediction. Since replies may now name a told Pattern, that reaction can follow Zeph bringing it up, not the User.
- **Suggested fix:** leave unless Users are offered Predictions they keep ignoring.

### Told Patterns are read on every reply

- **Kind:** risk
- **What:** for a User with a told Pattern, each reply reads all their Observations and Life Threads again (`PatternSharing.told_patterns`), and a waiting follow-up reads Observations and Predictions (`follow_ups_due_early`).
- **Impact:** none at today's size; a cost per reply once Users have hundreds of Observations.
- **Suggested fix:** read only the Observations of the told Pattern Types, in one query, when it shows up in reply times.

### The migrations were not run on a copy of real data

- **Kind:** note
- **What:** 0105 to 0109 ran on a fresh stack database and in tests that downgrade and migrate again. The main stack wasn't running, so `make db-copy` wasn't used.

### Design files changed by the agent again

- **Kind:** note
- **What:** `web/design/reference/AdminPatternCatalog.html` and its baseline now show the new catalog versions and three Prediction lines per card ("Prediction 1" to "Prediction 3", from the existing line part).

## 41 — Conditions are tagged on Observations (2026-11-26)

### The owner corrects the 10 drafted Tagging cases about Conditions

- **Kind:** risk
- **What:** the ten `cond-` cases in `tagging.yaml` were drafted by Claude (issue 41).
- **Impact:** a wrong label makes the Tagging Eval's read of the Conditions meaningless.
- **Suggested fix:** follow `docs/pattern-evals/adding-tagging-cases.md` (see "Audience, Stakes, State going in").
- [ ] Owner corrected the `cond-` cases

### The tagging prompt on production is kept if it was edited, without the "never guess" rule

- **Kind:** risk
- **What:** migration 0110 reloads `pattern_tagging_prompt` only where no Admin edited it. Code gives the model the three new lists either way, so an edited prompt fills them without being told to leave an unsaid one empty.
- **Impact:** guessed Conditions on real Observations, which issues 42 to 44 will narrow and ask on.
- **Suggested fix:** after the next deploy, check the backend log for "Kept the stored pattern_tagging_prompt"; if it is there, merge the new seed text in by hand before Pattern noticing is on. Minutes.

### The model guessed audience and stakes until the prompt said not to

- **Kind:** risk
- **What:** Eval Run `7f09461a` (live model): "one-to-one" for any story with one other person, and stakes "low" or "high" unsaid, in 4 of 10 cases. After two more prompt lines, run `bd350ed4` had no wrong Condition on three models. Ten drafted cases, one try each.
- **Impact:** a guessed Condition would narrow a Pattern on something the User never said (ADR-0031).
- **Suggested fix:** when the owner corrects the `cond-` cases, add a few messier ones and run them with Repeats. Under S$0.50 on the live model.

### A context line says "hers"

- **Kind:** failure
- **What:** run `bd350ed4` A, `cond-state-worn-out-before-call`: "holding Christmas at hers again" fails the "no he or she" check. The word means the sister's place, as the User said it.
- **Impact:** a case that tagged everything right fails.
- **Suggested fix:** the owner decides whether "hers" about someone the User named counts. No cost.

### Opus calls a high-stakes story unclear

- **Kind:** failure
- **What:** run `bd350ed4` B, `cond-high-stakes-visa-interview`: claude-opus-5.5 named ACH.WORTH.PERF and CTRL.UNCERT.PLAN together. Flash and Haiku named ACH.WORTH.PERF alone.
- **Impact:** only if the tagging model is changed to Opus; the draft may also be a fair "unclear".
- **Suggested fix:** the owner decides the label when correcting the drafts.

### State is emptied more widely when a past Conversation is tagged again

- **Kind:** risk
- **What:** the Safeguard rule asks whether the User had a Safeguard Event at or after the first message kept (`PatternTagger._tag`, `happened_from`), with no end time.
- **Impact:** `tag_again` on an old Conversation loses a state the User said, if they had a crisis any time later. It errs on the safe side. The other way round is possible only if Message Retention deleted the messages before the event.
- **Suggested fix:** store which Conversation a Safeguard Event happened in. A column and a migration; half a day.

### An Admin's own traces show the model's raw tagging answer

- **Kind:** risk
- **What:** the Model Call Log keeps full content for Users who are Admins (and for everyone where content is kept, as on a local stack). The tagging answer in it now holds a state going in.
- **Impact:** an Admin reading their own trace, or a developer on a local stack, sees a state. Other Users' calls keep no content, as before.
- **Suggested fix:** none needed unless content is ever kept for real Users.

## 42 — "Anyone would act the same" can match the new Conditions (2026-11-26)

### A sign against told with high stakes also counts for nothing

- **Kind:** decision for the owner
- **What:** a match makes an Observation situational whether it is for or against (the rule as before). CTRL.UNCERT.PLAN's sign against D2 is "plans heavily only where the stakes are concrete", so most D2 stories will be tagged high stakes and carry no weight.
- **Impact:** D2 rarely counts against the Pattern any more. That may be right (a crisis says nothing about the person either way), but D2 is then nearly a dead sign.
- **Suggested fix:** leave it, or reword D2 in a later version so it is about calm in a low-stakes unknown. Minutes; a new version and the owner's approval.

### A guessed "high" stakes now takes a story's weight away

- **Kind:** risk
- **What:** stakes high makes an ACH.WORTH.PERF or CTRL.UNCERT.PLAN Observation weightless. If the tagging prompt on production was edited and so lacks the "never guess" rule (see issue 41's finding above), guessed stakes now cost real evidence.
- **Impact:** those two Patterns could stay unnoticed for a User whose stories the model calls high stakes unsaid.
- **Suggested fix:** the same check as issue 41's finding, before Pattern noticing is on: after the deploy, look for "Kept the stored pattern_tagging_prompt" in the backend log and merge the seed text in by hand.

### Scoring and the ready gate can differ on a story kept under 0.3.0

- **Kind:** known limit
- **What:** scoring reads the `situational` mark stored with the Observation; the ready gate reads the catalog now. A high-stakes story kept under 0.3.0 (between issue 41 and this deploy) stays unmarked, so scoring counts it and the gate does not.
- **Impact:** small: only stories tagged in that gap. The Pattern can reach "suspected" on it but is stopped at the gate's "situational" check.
- **Suggested fix:** none now. If it matters later, one script can mark stored Observations again by the current catalog.

### "A real crisis" still has no tag

- **Kind:** known limit
- **What:** CTRL.UNCERT.PLAN's "anyone would" is "a real crisis". Only high stakes is a tag, and only when the User says what could be lost.
- **Impact:** a crisis story that doesn't say the stakes keeps its weight, unless an exclusion applies.
- **Suggested fix:** none; the tagging model is still told "anyone would" in words.

### The two older CTRL "anyone would" cases still fail, and one case errored

- **Kind:** owner task
- **What:** in Eval Run `50e37290`, `ctrl-anyone-dad-in-hospital` kept a "for" (I2) where the case expects "against", and `ctrl-anyone-flood-evacuation` kept nothing. Both failed before this issue too (run `4352910b`). The new rule did mark the hospital "for" situational, so it now counts for nothing. `ach-anyone-lost-big-bid` got no answer from the provider and was not run again.
- **Impact:** none on Users. The two cases expect something the model doesn't do.
- **Suggested fix:** the owner decides what each should expect now ("nothing", or "for · situational" with stakes high), following `docs/pattern-evals/adding-tagging-cases.md`.
- [ ] Owner corrected the two `ctrl-anyone-` cases

## 43 — Zeph asks about a missing Condition (2026-11-26)

### A missing Condition is only asked about while the Pattern is held back from ready

- **Kind:** decision for the owner
- **What:** the counter-test comes before the missing Condition (D6), and a Pattern that passes the ready gate leaves the Agenda. So once the counter-test is answered, Zeph asks about a Condition only if another check (situations, Conversations, score…) still holds the Pattern back.
- **Impact:** for a Pattern with plenty of evidence the Condition question is never asked; the gap is then only said when sharing (issue 44).
- **Suggested fix:** leave it and see in real use. If Conditions should be learned before sharing, add a ready check "nothing one-sided left to ask", or put the missing Condition ahead of the counter-test. An hour or two; the owner's call.

### Relationship and setting will be the usual one-sided Condition

- **Kind:** risk
- **What:** only the Condition with the most stories behind it is a need. Relationship and setting are tagged on nearly every story; audience, stakes and state only when said. On a tie the order is audience, stakes, relationship, power, stance, setting, state (my choice; the issue said "a fixed order").
- **Impact:** audience, stakes and state are asked about mostly when relationship and setting are already mixed.
- **Suggested fix:** leave it, or prefer the three newer Conditions outright. Minutes (`CONDITION_ORDER` and the pick in `missing_condition`).

### One Condition can be asked about several times

- **Kind:** decision for the owner
- **What:** a useful try closes one value. If the stories stay one-sided, the next unseen value of the same Condition opens (friend, then colleague, then partner). When a Condition has nothing left, the next most one-sided Condition becomes the need. State is the exception: one useful try closes every state, since the question is the same.
- **Impact:** more questions about Conditions over weeks than "one at a time" may suggest, still inside the usual limits (wait, rest, never two Conversations in a row).
- **Suggested fix:** leave it, or close the whole Condition after one useful try. Minutes.

### A "would it have gone differently" answer is weak evidence only if the model says so

- **Kind:** known limit
- **What:** code forces "what if" only for an answer to a numbered Thought Experiment. An answer to "would it have gone differently if…" is a "what if" answer when the tagging model marks it so.
- **Impact:** such an answer could be kept as a real story and count in full.
- **Suggested fix:** show the tagging step the "would it differ" questions asked in the Conversation, numbered like Thought Experiments, so code can force the kind. About an hour.

### The Reply Plan often doesn't pick the aimed Curiosity on a light opener

- **Kind:** owner task
- **What:** in Eval Runs `8a0bf7b9` and `fda65a7a`, on "kind of bored, talk to me" only deepseek-flash asked the one-to-one question; Haiku, Opus and deepseek-pro asked about the evening. In the running app flash asked it on the same opener.
- **Impact:** none on correctness: code wrote the right question each time. It shows how often the model takes the moment, which differs by model.
- **Suggested fix:** the owner corrects the three drafted cases (which opener, which rules), and uses Repeats before reading much into one run.
- [ ] Owner corrected the three `agenda-condition-` and `agenda-state-` cases

### The Judge's "never names a pattern" rule fails ordinary lines

- **Kind:** owner task
- **What:** it failed "that happens a lot" (Haiku) and a question about what a "nothing" night turns into (flash, first run).
- **Impact:** false fails on Agenda cases.
- **Suggested fix:** tighten the rule's wording in `understanding.yaml` so it is about Zeph claiming a tendency of theirs. Minutes.

### The production Reply Plan prompt will be kept, without the new line

- **Kind:** owner task
- **What:** migration 0111 reloads `reply_plan_prompt` unless edited. Production's is edited, so it stays and the log says "Kept the stored reply_plan_prompt". The new seed text says "Approach" and "When it says to ask openly how they were doing, never offer a mood or state yourself".
- **Impact:** small: the instruction code writes already says to name no state. The line is a second guard.
- **Suggested fix:** merge the two sentences in by hand after the deploy, with the other pending merges (`named_pattern`, `asked_for_patterns`).
- [ ] Owner merged the new Reply Plan prompt lines on production

## Comments

### 25 Nov 2026 — first triage with the owner (sections 01 to 19)

Every finding logged so far was sorted by risk. A copy of sections 01 to 16 that had been pasted in twice was removed. Findings logged after this note (issues 25 to 32) are not triaged yet.

**Moved into issues**

- `27-replies-that-mislead-the-user.md`: tool call sent as plain text (03); Zeph says a setting changed when it didn't (03); dropped topics come back (02); a picked Curiosity marked raised when never asked (02, 09).
- `28-migrations-keep-admin-prompt-edits.md`: migrations overwrite Admin prompt edits (02, 03, 08, 09).
- `29-understanding-eval-eight-failing-cases.md`: 8 Understanding Eval cases fail; `guess-checked-gently` can't pass (02).
- `30-owner-decisions-before-pattern-sharing-is-on.md` (owner decides first): the Read states an untested Pattern when asked (08); one story counts twice (09); the ruled-out topics list (07); deleting a disagreed Pattern forgets the "no" (18); a deleted quote may come back when a day is tagged again (13); the confirm and close numbers, Prediction wordings and unanswered Predictions (09); scoring counts narrowing evidence (07); Curiosity Check-ins ignore backing off (02); a told Pattern whose Pattern Type left the catalog (18).
- `31-tagging-eval-cases-brought-up-to-date.md` (owner corrects the cases first): owner corrects the drafted cases, 33 of 44, cases written for three types (14); no cases for exclusions and ruled-out topics (07) or Prediction outcomes (09); tag names written by hand (11); Eval environment copies fields by hand (02).
- `32-whole-pipeline-eval-can-be-trusted.md`: token limit, three cases never run, a case with nothing ready passes, no Pattern shared in any run (19).

**Tracked elsewhere**

- The pixel test hangs on Clerk's probes (03, 08, 18): `.scratch/redesign/issues/20-pixel-test-hangs-on-clerk-probes.md`.
- The Dashboard build fails on the first try (02, 14): `.scratch/mvp/issues/38-dashboard-build-fails-fetching-google-font.md`.
- The scripted User never answers Zeph (19): issue 26.

**Still open here, small, no issue yet**

- Needs and Moves page hints name the wrong step (01). Still true in `NeedFields.tsx:69` and `MoveFields.tsx:56`. A few minutes.
- Seed Copy is behind the design references, so Memories pixel tests fail (13). About half an hour.
- Run `make match-patterns` on production soon, while messages are still kept (16). No code; the owner's step.
- The owner reviews the design files agents changed (08, 17, 18) and the Whole-pipeline result panel that has no reference (19).

**Settled before this triage**

- Context lines call the User "she" (14): fixed in issue 22.
- The two old-Pattern findings in section 16: settled by issue 24.
- Evals of tagging keep nothing (13): issues 14 and 19 kept Observations, so this no longer holds.

**Let go, or wait for real use**

- The two never-Need findings (01): the fix adds a model call to every reply.
- The Eval cost estimate is off (14); an unclear case matches any pair (14).
- A Pattern keeps its first match; an unreadable matching answer reads as "no fit"; the unmatched review groups opposites; a one-User entry can point at that User; the general-description check can miss a detail; a dropped entry is judged by count only (all 16). Look again when there are more Users.
- A ready Pattern can be stale between two looks (07): issue 08 looks again before sharing.
- The check after the reply can fail after the Pattern was told (08): rare.
- The quotes a share used aren't stored; nothing reads a shared Pattern's score; stiff "it shows with…" wording (08).
- The floor is checked before the Predictions; confirmed Patterns reach only the Portrait (09).
- The switch shows while Pattern sharing is off (18).
- The Dashboard shows no share for the whole run; `make eval` leaves out Whole pipeline (19).
