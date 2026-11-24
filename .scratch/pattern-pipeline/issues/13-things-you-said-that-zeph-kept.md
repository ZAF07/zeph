# 13 — "Things you said that Zeph kept": Users see and delete their kept quotes

Status: ready-for-agent
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 20, 51, 52, 53, 54, 55, 58). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Quotes kept as evidence are the User's own words, so they must see and be able to delete them even while the Pattern is hidden (ADR-0027). A new list on the Memories page shows every kept quote with its context line (shown apart, as Zeph's note) and day, with no Pattern named. Deleting one removes the Observation and scores its Pattern again.

Wherever Message Retention is explained, Copy says plainly that quotes kept as evidence stay until deleted. Before Pattern noticing starts for an existing User, they are told what has changed.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The Memories page lists every kept quote with its context line and day, newest first, with no Pattern Type or Pattern named
- [ ] The quote and Zeph's note are shown apart
- [ ] A User can delete a quote; it is gone at once and can't come back from a Conversation end already under way
- [ ] The list works whether User Memory is on or off
- [ ] New Copy slots hold the list's title, explanation and empty state, and the retention wording names kept quotes
- [ ] An existing User is told what changed, in chat or on the Dashboard as agreed with the owner in this issue, before their first Observation is kept
- [ ] Admins see only how many kept quotes a User has
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments

Plan (24 Nov 2026, branch `pattern-13-kept-quotes`, worktree `ai-chat-companion-pattern-13`):

- **Owner's choices.** The list is a new eighth Memories tab, "Things you said" (`?tab=quotes`), last in the row. Users are told on the Dashboard: a notice on Home and Memories with a "Got it" button; no Observation is kept for a User until they press it. One rule for every User, new or existing.
- **Backend.** `UserMemoryService` lists a User's kept quotes (quote, context line, day; newest day first) and deletes one, then scores their Patterns again (`observations_deleted`). Routes `GET /kept-quotes` and `DELETE /kept-quotes/{id}`; the list doesn't look at User Memory. No Pattern Type or Pattern leaves the API.
- **Can't come back.** Scoring and deleting a quote each take a lock on the User's row, in one transaction with their reads and writes, so a Conversation end already scoring can't save a state worked out from a quote deleted meanwhile, and the deletion's own rescoring waits for it.
- **Told first.** New `users.pattern_noticing_told_at` (migration 0084). `/me` says whether to show the notice (Pattern noticing works for them and not told yet); `POST /me/pattern-noticing-told` sets it. The tagging step runs only once it is set.
- **Admins.** The Users API gives `kept_quote_count`; the user panel adds a "Kept quotes" row in "What Zeph holds".
- **Copy.** New slots: the tab name, heading, explanation, Zeph's note label, delete button, empty title and body; the notice's title, body and button; and `account.delete_data.kept_quotes`, shown after the retention line on Account ("Quotes Zeph keeps as evidence stay until you delete them."). A new slot, so the live text reaches existing databases.
- **Design.** Following the issue (as issue 10 did): new `Memories--tab-quotes.html` and `M-Memories--tab-quotes.html` built from the Patterns tab's parts, the tab added to every Memories reference, the sentence added to `Account`/`M-Account`, the notice sample in `States`, baselines reshot. The "Kept quotes" Admin row isn't drawn in `AdminUsers` (as with issue 12's rows), flagged for the designer.
