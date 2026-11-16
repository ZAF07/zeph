# 01 — Check-in polish: steady Due Times, "a few times a day", User Portrait for Check-ins

Status: ready-for-agent

Track: A (User side). Runs alongside track B (issues 03, 04).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

Make a User's Check-ins keep the rhythm they picked, and let them pick a faster one.

- **Steady Due Times.** After a Check-in is sent or skipped, the next Due Time is the first of "previous Due Time + n × frequency gap" that is still to come. Due Times missed while held back (e.g. a long pause) are not made up. A Due Time never falls within half a frequency gap of the last *sent* Check-in; one that would is moved to the end of that half gap. A User with no previous Due Time keeps today's behaviour for their first one. No backfill (platform not live).
- **"A few times a day".** A fourth Check-in Frequency, `a_few_times_a_day`.
  - Dashboard label: "A few times a day".
  - Chat wording: "at most a few times a day". The chat tool that changes the frequency accepts it (ADR-0006).
  - Its gap is set by Admins in Platform Settings like the other three. Default 6 hours, shown and editable on the admin Platform Settings page.
  - A data migration adds `a_few_times_a_day: 6` to the stored gaps where it's missing, because reading the gaps fails when a frequency is missing.
- **User Portrait for the standalone Check-in model.** Its input gains the User's User Portrait, next to the Memory Items and Conversation Summaries it already gets. The prompt is unchanged.
- **Conversation quiet gap seed default** becomes 15 minutes. This applies to fresh databases only.

Terms: Due Time, Check-in Frequency (`CONTEXT.md`).

## Acceptance criteria

- [ ] A User on "most days" whose Check-in is held back by Quiet Hours or a Conversation gets the following one at their original rhythm, not shifted by the hold-back (end-to-end test through scheduler ticks).
- [ ] After a long pause, the User gets one Check-in and then their normal rhythm, with no burst of missed ones.
- [ ] A Check-in is never sent within half a frequency gap of the last sent one.
- [ ] A skipped Check-in doesn't shift the rhythm.
- [ ] Pure decision-function tests cover: several missed Due Times, the half-gap pushing a Due Time, Quiet Hours across midnight, and a first Due Time with no previous one.
- [ ] A User can pick "A few times a day" on their Dashboard Check-ins page and in chat. Zeph confirms with "at most a few times a day".
- [ ] Admins see and edit the "a few times a day" gap on the Platform Settings page.
- [ ] The migration adds the missing gap to an existing database, and reading the gaps works afterwards (tested).
- [ ] The standalone Check-in model's input includes the User Portrait (test via the scripted chat model).
- [ ] The seed default for the Conversation quiet gap is 15 minutes.
- [ ] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` all pass.
- [ ] Verified in the running app with `/run`. Move DB timestamps back instead of waiting.

## Blocked by

None - can start immediately.

## Notes for parallel work

Track B also changes the Check-in decision and tick code and adds migrations. Whichever merges second rebases, and renumbers its migration if they clash.

## Comments
