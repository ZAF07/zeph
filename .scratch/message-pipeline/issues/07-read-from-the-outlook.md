# 07 — Zeph forms a Read from the Outlook

Status: in-progress
Lane: A
Blocked by: 05

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The heart of the review: Zeph stops only mirroring.

- **Outlook:** the Persona becomes two Admin-editable texts: its voice (today's Persona text) and its Outlook (new, plain prose, seeded with a starting text the owner can rewrite). The Outlook goes only into the Reply Plan's instructions; the voice stays in front of the Reply and Check-ins sent on their own. Both show on the settings page with hints.
- **Read:** the Reply Plan always forms a Read (Zeph's honest view of what is really going on, from the Outlook, the Understanding and memory) and decides whether to say it now: only when there is room (not mid-vent, in crisis or light chat; a vent is heard first, the Read comes once it is spent), it is worth saying (it adds something the User hasn't said) and it isn't a repeat (never the same Read twice in a Conversation). When the User asks for Zeph's view, it gives its deepest Read at once, not advice already given. The Read is offered as Zeph's view, never as fact.
- **Where we are:** the Reply Plan writes one line on where the Conversation is now ("venting, nearly spent", "asking for a view"); each Reply Plan sees the earlier ones.
- The Reply gets the Read at priority level 3 when it is to be said. Admins' own traces show the Read in full; the Model Call Log shape records only whether one was formed and said.

User stories covered: 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 22, 51, 52, 53, 63.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Persona** (`/admin/persona`): two tabs, Voice (reference `AdminPersona`) and Outlook (reference `AdminPersonaOutlook`, `?tab=outlook`), each with its own editor and save bar. Tabs work like the Memories tabs: clicking swaps the editor and sets `?tab=outlook`. Unsaved text in one tab is kept when switching to the other.
- **Model call trace** (reference `AdminModelCallTrace`): the Reply Plan step records "Read formed" and "Read said"; an Admin's own trace shows the Read and the where-we-are line in Content. Another User's trace shows only the two facts.
- **Shared references.** `AdminPersona` also draws 06's hints; `AdminModelCallTrace` also draws 05, 09, 11 and 14. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminPersonaOutlook` is yours alone.

## Acceptance criteria

- [ ] The Outlook is an Admin-editable setting with a hint, seeded, and a change applies from the next reply
- [ ] The Outlook reaches the Reply Plan's instructions and no other call; the voice still reaches the Reply
- [ ] Every Reply Plan carries a Read and whether to say it; a Read to be said reaches the Reply at level 3, one not to be said doesn't reach it
- [ ] The Reply Plan prompt states the three conditions and the when-asked rule
- [ ] Each Reply Plan writes a where-we-are line and earlier Reply Plans in the Conversation are in its input
- [ ] The Model Call Log records whether a Read was formed and said; an Admin's own trace shows its text
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Switching Persona tabs keeps unsaved text in the other tab (component test)
- [ ] `node design/compare.cjs AdminPersonaOutlook` prints PASS
- [ ] The tabs and the Read facts match `AdminPersona` and `AdminModelCallTrace`; full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-07-read`)

- **Outlook setting:** new `persona_outlook` Platform Setting (label "Outlook", hint as drawn), seeded with the drawn starting text. The `persona` setting becomes the voice (label "Voice"). The Reply Plan's instructions are the Outlook, then `reply_plan_prompt`. No other call gets the Outlook; the Reply and Check-ins keep the voice.
- **Read and where we are:** `ReplyPlanForm` gains `where_we_are`, `read` and `say_read` (stored in the existing `form` JSON, so no new column; old rows read as no Read). `say_read` counts only when there is a Read. A Read to be said goes into the Reply's level 3 (plan) section as Zeph's view, never as fact; one not to be said doesn't reach the Reply. Earlier Reply Plans in the Conversation are written for the next one with their where-we-are line, Read and whether it was said, so it doesn't repeat a Read.
- **Prompt:** `reply_plan_prompt` asks for the where-we-are line and the Read first, states the three conditions (room, worth saying, not a repeat) and the when-asked rule. Migration 0068 deletes the stored `reply_plan_prompt` so the new seed loads (platform not live; 0067 did the same for the Understanding).
- **Model Call Log:** `ReplyPlanShape` gains `read_formed` and `read_said` (JSON, old rows read as false). The Read's text shows only in an Admin's own Content, as today.
- **Web:** Persona page gets Voice and Outlook tabs (`?tab=outlook`), each with its own editor and save bar, drafts kept per tab. Trace facts gain "Read formed" and "Read said". Fixtures as drawn.

