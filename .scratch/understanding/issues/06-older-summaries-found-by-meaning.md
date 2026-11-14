# 06 — Older Conversation Summaries found by meaning

Status: in-progress

## Parent

`.scratch/understanding/PRD.md`

## What to build

"How did that job interview go?" works however long ago it was. Every Conversation Summary is embedded when written. When the Understanding's `look_up_past` has phrases, they are searched against the User's own Summaries; matches above an Admin-set closeness bar, up to an Admin-set number, go into the reply with their dates (beyond the newest few that always go in). An empty `look_up_past` searches nothing.

## Acceptance criteria

- [ ] New Summaries are embedded when written
- [ ] A `look_up_past` phrase brings a matching old Summary into the reply call; a weak match adds nothing
- [ ] Only the User's own Summaries are searched
- [ ] Closeness bar and number are Admin settings
- [ ] Deleting a Summary (or Delete My Data / Account Deletion) removes its embedding
- [ ] Tests at the webhook seam with the fake embedder; checks pass
- [ ] `/run`: a fact from an old Summary (timestamps shifted back) comes up when asked about

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`
