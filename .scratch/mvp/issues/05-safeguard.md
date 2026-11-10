# 05 — Safeguard

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Every incoming message passes through the Safeguard before anything else. It classifies risk (suicide or self-harm, danger to others, abuse, medical emergency, or none). On a crisis, the graph skips normal response composition and sends the Crisis Reply: Admin-edited wording that says plainly the Companion is an AI and not a replacement for real help, plus Helplines for the User's country, or the international fallback if none exist. A Safeguard Event (User, time, risk type — never message text) is recorded.

Admins manage Helplines per country and the international fallback, edit the Crisis Reply wording, and view Safeguard Events. Singapore Helplines and the international fallback are seeded from data files.

## Acceptance criteria

- [ ] The Safeguard runs on every incoming message, before the rest of the graph
- [ ] A crisis message gets the Crisis Reply with the User's country Helplines and no sticker; normal composition does not run
- [ ] A User whose country has no Helplines gets the international fallback
- [ ] Everyday stress or sadness is not treated as a crisis (covered by evals in issue 15; prompt states it)
- [ ] A Safeguard Event is saved with User, time and risk type only — no message text
- [ ] Admins can add, edit and remove Helplines per country and the fallback, edit the Crisis Reply wording, and view Safeguard Events
- [ ] Singapore Helplines (SOS 1767, IMH 6389 2222, emergency 995) and an international fallback are seeded from data files
- [ ] Seam 1 tests with a fake chat model cover: crisis → Crisis Reply with correct country Helplines, fallback, Safeguard Event saved without text, non-crisis → normal reply
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/03-onboarding.md`
- `.scratch/mvp/issues/04-admin-area-foundation.md`
