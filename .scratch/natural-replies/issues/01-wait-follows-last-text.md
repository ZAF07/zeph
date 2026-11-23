# 01 — The wait follows how the last text reads

Status: ready-for-agent
Track: A
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

Today every text restarts one 15s wait. Make the wait depend on how the User's latest text reads:

- **Finished**: ends with `?`, or is at least the "long" word count and ends with `.`, `!` or an emoji → short wait (2s).
- **Trails off**: ends with `...`, `…` or `,`; or its last word is in the trailing words list; or the whole text is one of the short openers in that list (`wait`, `ok so`, `lol`, `hmm`, …); or a photo with no caption → long wait (12s).
- **Neither**: anything else, including a sticker alone → middle wait (6s).

Matching ignores case and trailing spaces. An Album still waits for all its items, then is judged as one text. Start-over (a text before any reply has gone out drops the reply) stays as it is.

Admins set the three waits, the long-text word count and the trailing words list on the Platform settings page. Each setting has a hint (one or two sentences) saying what it is and how it changes Zeph's replies, e.g. *"How long Zeph waits for more when the User's last text ends unfinished ("and…", "so"). Longer means fewer cut-offs but slower replies."* `message_wait_seconds` stays as the **neither** wait with a rewritten hint.

A migration adds the new settings with their defaults and moves `message_wait_seconds` from 15 to 6 only where it is still the seeded 15 (as migration 0066 did). No User data is touched.

The deciding logic should be one small pure function (text + settings → kind and seconds).

## Acceptance criteria

- [ ] A text ending in `?` gets the finished wait; a 15+ word text ending in `.`, `!` or an emoji gets it too.
- [ ] A text ending in `...`, `…`, `,` or a trailing word, a short opener on its own, and a photo with no caption each get the trailing wait.
- [ ] Any other text, and a sticker alone, gets the neither wait.
- [ ] A text sent before any reply goes out still starts the reply over with every text.
- [ ] An Album is still answered as one, judged as one text once all its items are in.
- [ ] Admins see and can change all five new settings and `message_wait_seconds`, each with a non-empty hint of at most two sentences; bad values are refused (seconds 0–60, words 1–100, list not empty).
- [ ] A changed setting applies from the next text.
- [ ] Migration: new settings land with defaults; `message_wait_seconds` 15 → 6 only if unchanged; an Admin's own value is kept.
- [ ] Tests through the webhook (`FakeTimer.waits`), the Admin settings API, the migration and the Dashboard settings page; `pytest`, `ruff`, `ruff format`, `mypy`, and the `web/` checks pass.
- [ ] `/run`: in a worktree, post texts to the backend webhook and see a `?` text answered after ~2s and a trailing text held ~12s.
- [ ] `docs/message-pipeline/README.md` step 2 note and decision 19 updated to "Built".

## Blocked by

None - can start immediately.

## Comments
