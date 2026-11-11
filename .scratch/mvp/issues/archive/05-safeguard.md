# 05 — Safeguard

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Every incoming message passes through the Safeguard before anything else. It classifies risk (suicide or self-harm, danger to others, abuse, medical emergency, or none). On a crisis, the graph skips normal response composition and sends the Crisis Reply: Admin-edited wording that says plainly the Companion is an AI and not a replacement for real help, plus Helplines for the User's country, or the international fallback if none exist. A Safeguard Event (User, time, risk type — never message text) is recorded.

Admins manage Helplines per country and the international fallback, edit the Crisis Reply wording, and view Safeguard Events. Singapore Helplines and the international fallback are seeded from data files.

## Design

- `docs/design/zeph-admin.html`: Safety, Safeguard Events

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] The Safeguard runs on every incoming message, before the rest of the graph
- [x] A crisis message gets the Crisis Reply with the User's country Helplines and no sticker; normal composition does not run
- [x] A User whose country has no Helplines gets the international fallback
- [x] Everyday stress or sadness is not treated as a crisis (covered by evals in issue 15; prompt states it)
- [x] A Safeguard Event is saved with User, time and risk type only — no message text
- [x] Admins can add, edit and remove Helplines per country and the fallback, edit the Crisis Reply wording, and view Safeguard Events
- [x] Singapore Helplines (SOS 1767, IMH 6389 2222, emergency 995) and an international fallback are seeded from data files
- [x] Seam 1 tests with a fake chat model cover: crisis → Crisis Reply with correct country Helplines, fallback, Safeguard Event saved without text, non-crisis → normal reply
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/03-onboarding.md`
- `.scratch/mvp/issues/04-admin-area-foundation.md`

## Comments

**2026-11-11 — implemented on branch `feat/05-safeguard`.**

Decisions:
- Graph: `record_incoming → check_safeguard →` either `send_crisis_reply → END` or `compose_reply → deliver_reply`. The message is saved first (PRD flow step 2), then the Safeguard runs before anything else. The Crisis Reply is sent at once (no typing pause, not split) and saved in the Conversation, so the next reply sees it.
- The Safeguard gets the whole Conversation as **one transcript message** ("Earlier in the conversation… / Latest message to classify…"), not as chat turns. Found in `/run`: given chat turns ending after a Companion reply, DeepSeek wrote a companion-style reply instead of a label, so an abuse message right after a Crisis Reply was missed. With the transcript it answered `abuse` 4/4. The prompt now also says "You only classify. Never reply to the person".
- Reading the answer: the first crisis label anywhere in it wins (any case); else "none" means no crisis. An answer with **no label at all is asked again once; a second unlabelled answer counts as a crisis**, with risk type `unclear` ("Unclear answer" on the Dashboard). Missing a crisis is worse than a false alarm.
- If the Safeguard's model call fails, the User gets the usual "thoughts got tangled" reply and no normal reply.
- Helplines: one `helplines` table; the international fallback is the single row with no country (a unique partial index enforces one). It can be edited, never removed (409). Country Helplines can be added (go last in their country), edited, removed (with a confirm), and moved up/down within their country.
- **The fallback is shared only when the User's country has no Helplines** (or no country is set), as the PRD and this issue say. The design note "appended after the country list for everyone" was not followed; the page note now says "Shared with Users whose country has no Helplines".
- Safeguard Events store User, time, risk type and `helplines_country` (the country whose Helplines were shared, or null for the fallback) — needed for the design's "Helplines shown" column. No message text anywhere; a test checks the table's columns.
- Crisis Reply wording is the `crisis_reply` setting and must keep `{helplines}` (refused in plain words otherwise). Safeguard is the first entry in Core services, so its prompt and model are on Prompts & models.
- Seeding: `seed/helplines.yaml` loads only when the table is empty (first run), so a Helpline an Admin removes never comes back.
- Admin API: `GET/POST /helplines`, `PUT /helplines/international-fallback`, `PUT/DELETE /helplines/{id}`, `POST /helplines/{id}/move`, `GET /safeguard-events?risk_type=&days=`.
- Test fake: `ScriptedChatModel` routes calls whose instructions equal the Safeguard prompt to a separate script that defaults to "none", so older reply tests needed no change.

Caveats / follow-ups:
- **Owner must check the seeded Singapore Helplines** (SOS 1767, IMH 6389 2222, SCDF 995) before testers start (PRD).
- The dev database already had the old Safeguard prompt seeded; since no Admin had edited it, it was updated to the new seed text by hand. Seeding never overwrites an existing setting.
- "No sticker in the Crisis Reply" holds because stickers don't exist yet. Issue 10 must keep stickers off the crisis path and test it.
- Story 37 (Safeguard runs before the daily limit) belongs to issue 13; Safeguard evals to issue 15.
- Review judgement calls not acted on: the transcript framing words are in code rather than the editable prompt; repeated error-banner / table-header styles and the 422-message pattern across web components; repeated 404/422 handling in the Helpline routes.
- Pre-existing, not changed: right after a brand-new Clerk sign-in the first few API calls can get 401 for a moment.

Evidence:
- Seam 1: `tests/test_safeguard.py` (16: runs first on every message, crisis → Crisis Reply with SG Helplines and no reply call, seeded wording says it's an AI, fallback for GB and for no country, event without text + table columns, normal reply with no event, loose label reading, retry, two unlabelled → crisis, Crisis Reply in later history, prompt/model changes apply, failing Safeguard, prompt says stress/sadness is not a crisis), `tests/test_admin_safety.py` (20: seed, first-run only, add/edit/remove/move, fallback edit and can't remove, plain-word refusals, 404s, crisis reply setting and placeholder rule, core service, event filters and names).
- Seam 3: `CrisisReplyEditor`, `HelplinesManager` (12), `SafeguardEvents`, `SidebarNav`, `risk-types` and `countries` tests.
- `make check`: Python 102 passed; web 97 passed; ruff, ruff format, mypy, eslint, prettier, tsc clean.
- `/run` (Docker Compose, real Postgres, DeepSeek and Clerk): migration 0005 ran and seeded 3 SG Helplines + fallback. As a temporary Clerk Admin: Safety and Safeguard Events links in the sidebar; seeded rows shown; saving a Crisis Reply without `{helplines}` showed the refusal; added a UK Helpline, moved IMH up, filtered by country, removed it (with confirm). Real app wired with every production adapter except Telegram (a printing channel, so no one was messaged): "stressful… sad" and "this deadline is killing me lol" got normal replies; "pills… tonight" got the Crisis Reply with SG Helplines in ~1s; a UK User's abuse message got the fallback; the Events page listed both events with "Singapore" / "International fallback", filtered by Abuse, and showed no message text. Re-checked after review fixes. Temporary users, checkpoints and the Clerk account were deleted; seeded order restored.

## Completion

- Completed: 2026-11-11
- Commit: <to be filled in manually>
