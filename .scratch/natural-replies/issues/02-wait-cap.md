# 02 — A cap on the wait from the Message's first text

Status: ready-for-agent
Track: A
Blocked by: 01

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

However many texts a User sends, no Message waits more than a cap (20s by default) from its first text. Each wait is the rule's seconds (from 01) or the time left to the cap, whichever is shorter, never below zero. The cap counts from the first text of the Message, including texts that joined it through start-over.

`message_wait_cap_seconds` is an Admin setting with a hint, added by migration with its default. It can't be saved below the longest of the three waits.

## Acceptance criteria

- [ ] A long burst of trailing texts is answered by 20s after its first text.
- [ ] A Message that started over keeps counting the cap from its first text.
- [ ] A new Message after a reply has gone out starts its own cap.
- [ ] Admins see and can change the cap, with a hint; a cap below any of the three waits is refused.
- [ ] Migration adds the setting with its default; no User data is touched.
- [ ] Tests through the webhook (`FakeTimer.waits`), the Admin settings API, the migration and the Dashboard settings page; all Python and `web/` checks pass.
- [ ] `/run`: in a worktree, send trailing texts every ~10s and see the reply come by ~20s after the first.
- [ ] `docs/message-pipeline/README.md` step 2 note mentions the cap as built.

## Blocked by

- `.scratch/natural-replies/issues/01-wait-follows-last-text.md`

## Comments
