# 24 — Remove the Patterns kept before the Pattern Catalog and the code only they used

Status: completed
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Design: `docs/pattern-pipeline/README.md`. Raised by the owner on 25 Nov 2026, after issue 16: there are no paying Users (one friend is testing), so the old Patterns need not be carried over. Simple code matters more.

## What to build

Issue 16 kept every Pattern from before the Pattern Catalog: confirmed ones stayed confirmed, closed ones stayed closed, suspected ones became unmatched. This issue starts fresh instead.

- Delete the old confirmed and closed Patterns (the ones with no Pattern Type) and their evidence. Unmatched Patterns stay: they are part of the new design.
- After that a Pattern with no Pattern Type is always unmatched. Remove the code that only the old confirmed and closed ones used:
  - how the User took an offered Pattern (agreed, pushed back, brushed off) and when it was last offered;
  - the "pushed back" wait setting;
  - the matching command's handling of old confirmed and closed Patterns.

## Decisions (owner, 25 Nov 2026)

- **Unmatched Patterns stay**, with the keeping step, the Read thinking with them, the Admin review page (issue 17) and `make match-patterns TYPES=ID`.
- **Old unmatched Patterns are kept.** They look the same as the ones noted since.
- **Left idle, not removed:** offering a Pattern in a reply (`offer_pattern`), the Memories page's Patterns tab and the Portrait's "Patterns they agreed with". With no confirmed Pattern left they do nothing, until issues 08, 09 and 18 rewire them to Patterns of Pattern Types.
- **What the friend testing loses:** their confirmed Patterns disappear from the Patterns tab and from the Portrait, and Zeph offers no Pattern until sharing (08) is built. The migration asks for their Portrait to be rewritten without them, which happens within a minute of the deploy. Familiarity counts confirmed Patterns, so Zeph may rate how well it knows them a step lower.

## Acceptance criteria

- [x] After the migration no Pattern without a Pattern Type is confirmed or closed; unmatched Patterns and Patterns of Pattern Types are untouched
- [x] The reaction and last-offered columns and the pushed-back wait setting are gone from the database, the code and the Admin settings page
- [x] An unmatched Pattern still comes to mind in a reply and is still never offered
- [x] The keeping step still notes unmatched Patterns and adds evidence to them
- [x] `make match-patterns` still matches unmatched Patterns and tags their evidence again
- [x] The Patterns tab shows its empty state and the Portrait is written without Patterns
- [x] The docs (`CONTEXT.md`, ADR-0024, the pipeline READMEs) and issues 08, 18 and 20 no longer say old Patterns are kept
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Comments

### 25 Nov 2026: built and checked

**What was built.** Migration 0097 deletes the confirmed and closed Patterns with no Pattern Type (their evidence, in-mind rows and Explorations go with them), asks for a Portrait rewrite for Users who had a confirmed one, drops `patterns.last_offered_at` and `last_reaction`, and deletes the `pattern_pushed_back_wait_days` setting. Code removed: `PatternReaction`, the two fields on `Pattern`, `may_come_to_mind`, the state-words table, the setting and its Admin form row, the matching rule for closed Patterns, and the unused time zone on `describe_pattern`. The test of migration 0092's carry-over was replaced by a test of 0097 and a small one that 0092 still makes suspected Patterns unmatched; the 0069 test of `last_offered_at` went with the column.

**Not changed, on purpose.** `offer_pattern`, the Patterns tab, `list_confirmed` / `delete_confirmed` and the Portrait's Patterns line stay, idle. The seeded `reply_plan_prompt` and `pattern_keeping_prompt` still mention confirmed and closed Patterns and reactions: changing them would reset Admin edits, and issue 08 rewrites that part.

**Shared files touched:** the platform settings seed, `PlatformSettingsForm.tsx`, a new migration (0097; renumber if another lands first).

**Checks.** `make check`: ruff, format and mypy clean; pytest and the Dashboard tests pass (counts in the Completion section). Review by two agents (standards, spec); findings fixed: stale docstrings and doc lines, a misleading name, the Portrait rewrite request, the lost 0092 test, issue 20's second finding.

**Evidence from the running app** (worktree stack, made-up User, real model, 25 Nov 2026):

1. *Migration.* Database taken back to 0096 and seeded with one unmatched, one confirmed ("agreed") and one closed ("pushed_back") Pattern with no Pattern Type, two evidence lines each, and a closed Pattern of `ACH.ABSORB.PULL`. After the backend restarted on 0097: only the unmatched one (2 evidence lines) and the `ACH.ABSORB.PULL` one were left; 2 evidence rows in all.
2. *Columns and setting.* `last_offered_at` and `last_reaction` are not in `patterns`; no `pattern_pushed_back_wait_days` row. The Admin settings page shows "Pattern closeness bar" and no pushed-back wait.
3. *Replies.* Message "the app has me again. skipped lunch, and I snapped at mum…" through the webhook. The Reply Plan model was shown "[1] (unmatched) When something grabs them, everything else goes quiet…"; the saved plan has that Pattern in `patterns_used`, `pattern_offered` null, and a Read built on it. The reply did not name a pattern.
4. *Keeping.* When that Conversation ended, the keeping step added a third evidence line to the unmatched Pattern and wrote its general description; it stayed unmatched. Tagging kept two `ACH.ABSORB.PULL` Observations and the Pattern of that Pattern Type moved to noticed.
5. *Matching.* `make match-patterns TYPES=ACH.ABSORB.PULL`: "1 Patterns looked at, 1 matched, 1 Conversations tagged again, 1 Observations kept, 1 evidence days with no messages left"; the Pattern kept its state and got the link.
6. *Patterns tab and Portrait.* With the confirmed Pattern deleted, the Patterns tab shows "No patterns yet". The Portrait model was given "Patterns they agreed with: None yet." A second run of the migration with a confirmed Pattern set the Portrait's rewrite request, and the backend rewrote it about a minute later. The Admin's Manage panel shows Confirmed Patterns 0, Noticed Patterns 1, Unmatched Patterns 1.
7. *Docs.* `CONTEXT.md`, ADR-0024, the pipeline and message-pipeline READMEs, and issues 18 and 20 updated; issue 08 needed no change.

The pixel test was not run: no component layout or design reference changed (one settings row removed, which no reference shows).


## Completion

- Completed: 2026-11-25
- Checks: pytest 2221 passed; Dashboard 972 tests passed; ruff, format, mypy, lint and typecheck clean
- Commit: <merge commit, filled in after the merge>
