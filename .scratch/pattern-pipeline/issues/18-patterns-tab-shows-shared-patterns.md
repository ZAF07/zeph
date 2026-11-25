# 18 — The Patterns tab shows Patterns being tested, confirmed, disagreed with and that didn't hold up

Status: ready-for-agent
Track: B
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 45, 46, 47, 48, 49, 50). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Users see a Pattern only once the Companion has told them about it. The Memories page's Patterns tab shows: shared ones as being tested, with their quotes, the Prediction and how it went; confirmed ones with their evidence and Prediction record; contested ones as "you disagreed", where the User can delete it or turn silent gathering off; and closed ones only if they were ever shared, as "didn't hold up". Never a score or percentage: words and evidence only. Noticed, suspected, ready and unmatched Patterns never show.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The tab shows shared, confirmed, contested and once-shared closed Patterns, each under its own wording
- [ ] Each shows its quotes grouped by part of life, its Prediction and how it went
- [ ] No score, percentage or state name from the code is shown
- [ ] Noticed, suspected, ready, never-shared closed and unmatched Patterns are not returned by the API at all
- [ ] A User can delete any shown Pattern; it is gone at once and the User Portrait is rewritten without it
- [ ] The contested section has the silent gathering switch
- [ ] New Copy slots hold every heading, label and empty state
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments

- 25 Nov 2026 (issue 24): the line "Confirmed Patterns from before this work still show" was removed. The owner had the confirmed and closed Patterns kept before the Pattern Catalog deleted, so the tab is empty until this issue fills it from Patterns of Pattern Types. The tab, `GET /api/patterns` and `DELETE /api/patterns/{id}` still read the old confirmed rows (`list_confirmed`, `delete_confirmed`); rewire them here.
- 25 Nov 2026 (from issue 08): the states shared and contested exist now, with `patterns.shared_at`, `predictions` and `pattern_reactions`. The silent gathering switch is `contested_gathering_enabled` on `/api/me` (PATCH to change), already on Account & privacy as "Keep noticing after I disagree" (`PreferenceSwitch`), shown while `pattern_sharing_works`. Which quotes a share used isn't stored: show the Pattern's Observations. Deleting a shared or contested Pattern has no API yet (`delete_confirmed` only).
- 25 Nov 2026 (from issue 09): the state confirmed is reached now, and a Pattern closed after it was shared stays closed (`patterns.shared_at` is set, so "didn't hold up" = closed with `shared_at`). Why it was confirmed or closed is `pattern_moves.reason`. How a Prediction went is `predictions.outcome` (`came_true`, `did_not`, `not_come_up`, `not_followed_up`; empty while open) with `outcome_at`; a Pattern can have several Predictions, oldest first. Deleting a confirmed Pattern of a Pattern Type still has no API, and the Portrait reads confirmed ones through `list_of_pattern_types`.
- 25 Nov 2026 (status, branch `pattern-18-patterns-tab`): built and checked in the running app, not archived yet. **Waiting on issue 09** for one thing: how a Prediction went. Nothing stores it on main, so the API sends `outcome: null` and every Prediction reads "Zeph hasn't asked how it went yet". Once 09 is merged: rebase, send `prediction.outcome` in `to_pattern_response` (`adapters/http/dashboard_api.py`), make `PredictionResponse.outcome` a `PredictionOutcome`, check the four wordings in the running app, then tick, archive and merge. The tab already has Copy for came true, didn't, hasn't come up and never asked.

What was built (25 Nov 2026):

- **Backend.** `told_patterns` in `core/told_patterns.py` (pure) picks the Patterns a User may see: shared, confirmed, contested, and closed only with `shared_at`, of a Pattern Type in the catalog now. `UserMemoryService.list_told_patterns` and `GET /api/patterns` return each with its state, approved wording, where it shows, when it was told, quotes grouped by Life Thread and Predictions, newest first. No score. `DELETE /api/patterns/{id}` deletes only a Pattern they were told (404 otherwise), under the User's lock, then scores again and asks for a new Portrait. The old `delete_confirmed` is gone; `list_confirmed` stays for the Portrait until 09 replaces it.
- **Dashboard.** `PatternsList` shows four headings (Being tested, Confirmed, You disagreed, Didn't hold up), each only when it has a Pattern; `PatternCard` is one Pattern. Under "You disagreed" is the same switch card as on Account & privacy.
- **Copy.** `memories.patterns.*`: intro, four headings, told on, where it shows, two labels, "Other moments", quote marks, asked on, five "how it went" wordings, delete label, empty title and message. The old `lead`, `agreed`, `based_on`, `evidence_when` and `empty_body` slots are removed; the changed texts use new keys so no migration is needed.
- **Design.** As issues 10, 13 and 08 did: the Patterns panel in `Memories--tab-patterns.html` and `M-Memories--tab-patterns.html` was redrawn from the old Patterns card's parts, the Memories group heading and the Account switch card; the empty state words in `States.html` changed; three baselines reshot (only those three changed).

Decisions made while building:

- **Deleting a Pattern deletes its quotes too**: the Observations whose first Pattern Type is its own. Otherwise the next scoring would start it again from the same words and it could be told again. An unclear quote that names it second stays (it belongs first to another Pattern). The tab's intro says so.
- **Which quotes show**: the ones that may be quoted back when sharing (`may_be_quoted`): clear evidence for it from their own life. Evidence against, unclear, "what if" answers and ones where anyone would act the same are left out. The quotes a reply really used aren't stored (issue 08).
- **Part of life** is the Life Thread's title; quotes in no Thread go last under "Other moments".
- **Where it shows** (narrowings) is on the card, in words said to the User ("people above you").
- **The switch** shows whenever they have a Pattern they disagreed with, also while Pattern sharing is off for them, since it still decides what the tagging step keeps.
- **Left from review:** the backend's state order and the tab's heading order are each written once on their side; the tab's row markup copies the old card (it is the drawn design); a told Pattern whose Pattern Type left the catalog isn't listed.
