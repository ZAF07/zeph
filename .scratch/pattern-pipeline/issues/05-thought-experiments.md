# 05 — Thought Experiments: Admins manage them, Zeph asks them in chat and as a Check-in

Status: ready-for-agent
Track: A
Blocked by: 04

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 6, 8, 71, 72, 73, 74, 75). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A Thought Experiment is a made-up scenario written to tell two look-alike Pattern Types apart. Admins manage them on a new Dashboard page: wording, the two Pattern Types it separates, how sensitive it is, whether it is a starter, on or off. They are archived, never deleted. A check on save flags leading wording. A first set is loaded from a seed file.

For an Exploration, code picks the Thought Experiment for the look-alike pair with the most unclear evidence, at most one per Pattern per week (Admin-set). It is asked as a Curiosity in its own words, in chat or through the existing Curiosity Check-in Kind and its weekly limit. The User's answer becomes an Observation of the "what if" kind.

Also in this issue: the agent drafts the first set (about 30, each naming its pair) and writes `docs/thought-experiments/README.md`: how they work, where to find material, how to write a good one, how to manage them, and what an edit changes. The owner then refines the set.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] Admins can add, edit, switch off and archive Thought Experiments on the Dashboard; an archived one is never asked and past tries still show it
- [ ] Each has its wording, two Pattern Types, sensitivity, starter flag and on/off, each with a hint
- [ ] Saving one with leading wording shows a warning the Admin can act on
- [ ] The first set is loaded once from the seed; a seed never overwrites an edited one or brings back an archived one
- [ ] Code picks the Thought Experiment for the pair with the most unclear evidence and never more than the Admin-set number per Pattern per week
- [ ] It is asked in its own words in chat, and can be sent through the Curiosity Check-in Kind within its weekly limit
- [ ] An answer is tagged as an Observation of the "what if" kind
- [ ] `docs/thought-experiments/README.md` exists and covers how they work, sourcing, writing, managing and what an edit changes
- [ ] The owner has reviewed the drafted first set (comment on this issue when done)
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `04-explorations-and-the-agenda.md`

## Comments

Plan (24 Nov 2026, branch `pattern-05-thought-experiments`, worktree `ai-chat-companion-pattern-05`; started once issue 04 was archived, merged and torn down):

- **Store.** `thought_experiments` (migration 0089): wording, the two Pattern Types it tells apart, sensitivity (low, medium, high, as a Curiosity's), starter, on, archived (when), a seed key. Never deleted. `exploration_tries.thought_experiment_id` links a try to the one it asked, so past tries keep showing it after an edit or archive.
- **Seed.** `seed/thought_experiments.yaml`, each with a `key`. At start, code adds each seeded one whose key isn't stored yet, in any state, so a seed never overwrites an edit and never brings back an archived one.
- **Admin page** `/admin/thought-experiments`, from the card-list template: one card each with Wording, Tells apart (two Pattern Types from the catalog), Sensitivity, Starter and On, each with a hint; add, edit, switch off and archive (with confirm); archived ones listed apart, read only, with how often they were asked. New reference `AdminThoughtExperiments.html` from card-list parts only, its baseline, the menu link on the other admin references (as issues 10 and 14 did).
- **Leading wording.** A pure code check on save (no model call): phrases that suggest the answer ("wouldn't you", "surely", "most people would", …) or a question offering only one side. Save is refused with the flags unless the Admin presses "Save anyway"; the card shows each flag with what to change.
- **Picking (code).** A new way between "would it differ with someone else" and "notice this week": for an unclear need, code takes the look-alike pair with the most unclear Observations of that Pattern, and picks a Thought Experiment for that pair that is on, not archived and never put to this User, starter or not. Never more than `thought_experiments_per_pattern_per_week` (1, Patterns section, hint, Eval override) per Pattern in 7 days (asked or waiting). None to pick: the next way is used. Other needs skip this way.
- **Asking.** It is an aimed Curiosity whose question tells the Reply to put the made-up situation in its own words (quoted), with the Thought Experiment's sensitivity. So it is asked in chat as any aimed Curiosity, or by the Curiosity Check-in Kind under its weekly limit. Switching one off or archiving it closes its waiting Curiosities at once; the Agenda also closes any left.
- **"What if" answers.** The tagging step is shown the Thought Experiments asked in the Conversation, numbered; an Observation that answers one says its number, and code makes its kind "what if" answer. Tagging prompt reloaded from the seed.
- **Docs.** `docs/thought-experiments/README.md`; the first set (~30, every look-alike pair of issue 15's catalog, one starter per area) for the owner to review.
- **Tests.** Pure tests for the leading check, picking and the weekly limit, the way order; HTTP-edge tests for the Admin API, seeding, the Conversation-end chain and tagging; web tests for the manager.

Decisions made while building (24 Nov 2026):

- **Migration is 0091.** Main took 0089 (tagging context without he or she) and 0090 (DeepSeek served model names) while this was built. Its downgrade removes no User data: tries only lose the link.
- **The tagger reads the words as asked** (the aimed Curiosity's question), not the Thought Experiment's current wording, so an edit mid-Conversation can't mislead it. Only a whole number matches a Thought Experiment shown; `true` doesn't count as 1.
- **The pair is picked across the Pattern's unclear stories**, as the PRD says ("the pair with the most unclear evidence"); the try still aims at the top unclear story, so the "way" order of that need moves on as before.
- **The weekly limit is per Exploration**, which is one per Pattern (unique) and goes with it.
- **No one-sided-question check.** The leading check is a word list only (phrases that suggest the answer, words that make a choice sound bad, with endings: "weakness" counts). "Save anyway" covers a word that is fine where it is. Noted in the guide's limits.
- **Pattern Type options show IDs only**, so a long name is never clipped in the select; names are on the Pattern Catalog page.
- **Starter and On are switches** (the references draw on/off as switches, not tick boxes), saved with the card's save bar.
- **Design files.** As issues 10 and 14 did, the issue's "add the reference" was followed: new `AdminThoughtExperiments.html` built only from card-list and field-row parts, its baseline and lines in `routes.json` and `manifest.json`, and the menu link on the other twelve admin references. `shoot.cjs` on the untouched references changed no baseline; after the link it changed none either, since the sidebar is cut at the 800px viewport above the new link.
- **Review (standards and spec).** Fixed: migration number and downgrade, tagger words as asked (and no per-item lookups), `true` ≠ 1, a named `way_after`, shared "times asked" words and save-failed text, a checked sensitivity instead of a cast, fixture import order. Left as judgement calls: `close_waiting` lives on the Thought Experiment repository (it closes only the Curiosities of its tries), the API counts all asks to answer for one (Admin page only), `LeadingWordingConfirm` borrows the remove confirm part (no warning part exists in the design).
