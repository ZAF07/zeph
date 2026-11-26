# The Pattern Catalog: an Admin guide

What the Pattern Catalog is, what each field of a Pattern Type does, how to
change one or add one, and what each change does to the system. For how the
whole Pattern pipeline works, see `docs/pattern-pipeline/README.md`. For why
the catalog lives in git and not on the Dashboard, see ADR-0025.

## What it is

The Pattern Catalog is the list of every kind of Pattern Zeph may look for,
test and one day share. Each entry is a **Pattern Type**: one way a person
tends to act in one kind of situation, and why. Zeph can only notice, score
and share Patterns of a Pattern Type in the catalog. Anything else it notices
is kept as an unmatched Pattern and is never shared as a Pattern.

Each Pattern Type has the same shape: **if** (the situation that sets it off),
**then** (what the person does) and **function** (what it does for them). For
example: if someone close goes quiet, then they read it as trouble and reach
out to check, to feel secure in the bond.

There are fifteen, three in each of five areas:

| Area | Pattern Types |
|---|---|
| Conflict | CONF.AVOID.BELONG, CONF.DEFEND.SELF, CONF.WITHDRAW.HURT |
| Approval | APPR.GIVE.NEEDED, APPR.CONFIRM.CHOICE, APPR.HIDE.BURDEN |
| Control | CTRL.UNCERT.PLAN, CTRL.SELF.RELY, CTRL.OPEN.FREEDOM |
| Achievement | ACH.WORTH.PERF, ACH.ABSORB.PULL, ACH.GOAL.MOVE |
| Relationships | REL.CHECK.SECURE, REL.DISTANCE.INDEP, REL.MOOD.FIX |

All fifteen were written as drafts and approved by the owner (Zaf) on
24 Nov 2026. ACH.WORTH.PERF and CTRL.UNCERT.PLAN 0.4.0 (high stakes as an
`anyone_would_when` tag) were approved on 26 Nov 2026.

## Where it lives

One YAML file per Pattern Type in `src/companion/seed/pattern_catalog/`. The
backend loads the folder when it starts. Admins read the catalog on the
Dashboard (Admin → Pattern Catalog) but can't edit it there. A change is a
change to a file, reviewed and deployed like code.

The whole catalog loads or none of it does. If any file is wrong, the backend
prints every problem with its file and field, and starts on the catalog as it
was last loaded. Zeph keeps replying either way.

## The fields

| Field | What it is | What reads it today |
|---|---|---|
| `id` | A stable ID like `CONF.AVOID.BELONG`: area, driver, behaviour. Never changes once loaded. | Everything. Observations and Patterns are stored under it. |
| `version` | Like `0.3.0`. Every loaded version is kept and never changes. | The loader. Each Observation keeps the version it was tagged under. |
| `area` | conflict, approval, control, achievement or relationships. | The Dashboard groups and orders by it. |
| `name` | A short plain name. | The Dashboard; look-alikes that name this type show it. |
| `status` | draft, approved or archived. See "Review status" below. | The Dashboard only. Tagging looks for every Pattern Type whatever its status; the Ready gate and sharing will read it (not built yet). |
| `approved_by`, `approved_on` | Who approved it and on what day. Both or neither; only for approved or archived. | The Dashboard. |
| `definition` | What the Pattern is, in two or three sentences, including what it is *not*. | The tagging model. |
| `if`, `then`, `function` | The situation, the behaviour, and what it does for the person. | The tagging model; the Dashboard card title. |
| `frameworks` | Published ideas the Pattern Type draws on. For the owner and a future reviewer only. | The Dashboard. Never sent to a model or shown to a User. |
| `signs` | What counts **for** it. Each has an `id` (I1, I2…), `text`, `strength` (weak, moderate, strong) and `part` (situation, inside, behaviour). | The tagging model picks one per Observation; scoring turns its strength into points. |
| `signs_against` | What counts **against** it. Same fields, IDs D1, D2…. | Same as signs; against Observations take points away. |
| `look_alikes` | What it can be mistaken for. Either another `pattern_type` (by ID) or a `name` for something outside the catalog (e.g. healthy focus), with `tells_apart`. | The tagging model: when it can't tell two look-alikes apart it names both, and the Observation is unclear. |
| `anyone_would` | When anyone would act this way, so it says nothing about the person. | The tagging model. |
| `anyone_would_when` | Optional. The same, as situation tags: `relationship`, `power`, `setting`, `stance`, `audience`, `stakes`, `state_going_in`. Each is a list of values from that tag's fixed list (e.g. `stakes: [high]`); a value outside it, or an empty list, stops the load. A match needs every tag it names, and an Observation with one of those tags empty never fits. | Code: an Observation whose tags fit is situational and carries no weight. |
| `exclusions` | When it must not be shared, and whether evidence from then is `ignored` or `counted_not_shared`. | The tagging model, which says which exclusions apply to a User now (from their open Life Threads and latest Day Summaries), and the ready gate: while one applies the Pattern is never ready, and with `ignored` the Observations tagged then carry no weight. |
| `approved_wording` | The Pattern in warm, plain words, as Zeph's view. | Given to the Reply Plan, the reply, a Check-in that shares it and the tagging step (to read how they took it), once the Pattern is ready or told. A change applies from the next reply. |
| `prediction_wordings` | A list of Predictions: each is one thing to notice next time, with a `{placeholder}` the model fills. Each tests a **different side** of the Pattern. At least one; write three. | Code picks one: the first when the Pattern is shared, then the first this User's Pattern hasn't had (once all were given, the one given longest ago). The reply or Check-in puts the User's own person or thing in the placeholder. The Prediction is kept as it was worded to them, with its number. |
| `numbers.situations_needed` | Situations (Life Threads) needed before it can be Ready. | The ready gate: the Pattern needs this many situations, or the Admin-set number when that is more. |
| `numbers.base_rate` | A first guess at how common it is, 0 to 1. | Not read yet: kept for when the score becomes a probability. |

Numbers that apply to every Pattern Type (sign points, kind of evidence,
half-life, score bars) are Platform Settings, not catalog fields. Change them
on the Dashboard's Platform settings page.

## Writing rules

- **Our own words.** Never copy items from a published questionnaire or test.
  Name the idea under `frameworks`; write the signs fresh.
- **No clinical language** anywhere a model or User may read it: no
  diagnoses, no "disorder", "trauma", "anxious", "avoidant", "attachment"
  and similar. A test (`tests/test_pattern_catalog_reader.py`) checks a list
  of such words in every field except `frameworks`.
- **Signs are things a person could say.** "Sends 'are we okay?' after a slow
  reply" can be quoted; "has low self-worth" can't.
- **Five or so signs, two or more against**, each with a strength. Strong
  means it nearly settles it on its own; weak means it only adds up.
- **Look-alikes go both ways.** When A names B, B must name A, and each
  `tells_apart` says the same difference from its own side. A test checks
  that every pair is named both ways; a person checks the wording.
- **Relationships get the longest exclusion lists.** Abuse, threats and
  controlling behaviour are never a Pattern: they stay with the Safeguard,
  and evidence from them is `ignored`.

## How to change a Pattern Type

1. Edit its YAML file.
2. Give it a new `version`. Any change at all needs one, even a comma: a
   stored version never changes, so the load refuses a changed file that
   keeps its version (the old catalog stays). Use the middle number for a
   change of meaning (0.2.0 → 0.3.0) and the last for wording (0.3.0 → 0.3.1).
3. If you add, remove or rename a look-alike, change the other Pattern Type
   too, and give it a new version as well.
4. Run `uv run pytest tests/test_pattern_catalog_reader.py tests/test_pattern_catalog.py`.
   `test_the_design_fixture_is_the_catalog_admins_read` will fail: refresh
   `web/src/lib/design-fixtures/seed-pattern-catalog.json` so the Dashboard's
   design fixture matches, and update `web/design/reference/AdminPatternCatalog.html`
   if a card the reference shows changed (see `web/design/README.md`).
5. Run the Tagging Eval (it costs money: check the estimate first), and add
   or fix its cases in `src/companion/seed/evals/cases/tagging.yaml`.
6. Deploy. Then check the backend's start log, or the Pattern Catalog page,
   for the new version.

## Writing and correcting Predictions

Every Pattern Type has three Predictions under `prediction_wordings`. They
were drafted by Claude on 25 Nov 2026 and are yours to correct.

**Why three.** With one Prediction, a "new" one was the old one in other
words, so "two came true" was one test passed twice. Now two that came true
are two different tests: a Pattern is confirmed by Predictions only when two
*different* wordings came true (and more came true than didn't).

**What makes a good set.** Each one looks at the Pattern from a different
side:

1. **The moment itself.** What they do when the situation comes up. ("Next
   time {person} asks for something you'd rather not do, notice whether you
   say yes before you've decided.")
2. **The cost, or what comes after.** What it is like later. ("Next time you
   go along with {person} on something, notice how you feel about it a few
   hours later.")
3. **The edge.** Where the Pattern should *not* show, or its other side.
   ("Next time you disagree with someone you're not close to, like {person},
   notice whether saying so feels any easier.")

**Rules for each one.**

- One thing to notice, in one sentence, starting from a moment that will
  come up in ordinary life within a week or two.
- Ask them to **notice**, never to change or try something. A Prediction is
  a test, not homework.
- It must be able to come out either way. If any answer would fit the
  Pattern, it tests nothing.
- Use one `{placeholder}` (like `{person}` or `{task}`) where the reply
  should put their own person or thing.
- Plain, warm words. No clinical language (the same test checks them).

**How to correct them.**

1. Edit the list in the Pattern Type's YAML file. Change the words of one in
   place; add a new one at the end; don't reorder them.
2. Give the file a new `version` (the last number for wording: 0.4.0 →
   0.4.1).
3. Follow steps 4 and 6 of "How to change a Pattern Type" above. No Eval
   run is needed for a wording change: the tagging step never reads
   Predictions' wordings.

## How to add a Pattern Type

What to add comes from the Dashboard (Admin → Unmatched Patterns): what Zeph
keeps noticing that fits no Pattern Type, as general descriptions with how
many Users each appears for. Mark an entry "New Pattern Type" when you decide
to write one for it, "Folded" (naming the Pattern Type) when an existing one
should cover it, or "Dropped". A mark is only a note for Admins: nothing
changes until the file below is written and deployed.

Copy a file in the same area and change everything. Pick an ID in the same
shape (`AREA.DRIVER.BEHAVIOUR`), set `version: 0.1.0` and `status: draft`. Add
it as a look-alike to every Pattern Type it can be mistaken for, with new
versions for those. Add at least one Tagging Eval case for it and one against
it (a test needs both for every Pattern Type). Then follow steps 4 to 6 above.

After the deploy, run `make match-patterns TYPES=<the new ID>` on that stack
(for production, on the server). It asks a model, for each User's Pattern
with no Pattern Type that isn't matched yet, whether it fits the new Pattern
Type. Where one does, the Conversations behind its evidence that Message
Retention still keeps are tagged again against it, so old evidence becomes
Observations, checked and scored like any other. It makes real model calls
(a few per Pattern), prints only IDs and counts, and leaves out Users for
whom Pattern noticing doesn't work or who haven't pressed "Got it"; run it
again later for them. `make match-patterns` with no `TYPES` matches against
the whole catalog.

## What each change does

| Change | What happens |
|---|---|
| New version of any field | Loaded on the next start. Older versions stay stored; Observations keep the version they were tagged under. |
| A sign's `strength` | Scores shift on the next scoring (each Conversation end, or when evidence is deleted): scoring reads the strength from the current version, also for Observations tagged under an older one. |
| A sign removed or its `id` changed | Observations that named it count nothing from the next scoring. The tagging step can't pick it any more. |
| `definition`, `if` / `then` / `function`, signs' `text`, `look_alikes`, `anyone_would` | Changes what the tagging model looks for, from the next Conversation end. Past Observations are not tagged again. Run the Tagging Eval. |
| `anyone_would_when` | Changes which new Observations are situational. Past ones keep how they were marked, so scoring counts them as before; the ready gate reads the current version, so there a past Observation that fits the new match stops counting. |
| `exclusions` | Changes what the tagging step may flag, from the next Conversation end. An exclusion taken away stops applying at the User's next tagged Conversation. Observations already marked excluded stay so. |
| `numbers.situations_needed` | The ready gate uses it from the next Conversation end; a ready Pattern that no longer has enough situations goes back to suspected. |
| `approved_wording`, `prediction_wordings` | Used from the next time a Pattern is shared, followed up or given a new Prediction. A follow-up Curiosity already waiting keeps the words it was written with, and a Pattern already told keeps the wording it was told in (the User sees that wording on their Patterns tab). Keep the order of `prediction_wordings`: a Prediction remembers its place in the list, so moving one makes Zeph think a different one was given. Add new ones at the end. |
| `numbers.base_rate` | Nothing yet. |
| `status` draft → approved | Its Patterns may become ready from the next Conversation end. A draft gathers evidence silently and is never ready; approved → draft sends a ready Pattern back to suspected. Needs `approved_by` and `approved_on`. |
| `status` → archived | Today nothing: the tagging step is sent every Pattern Type in the catalog, archived ones too, so an archived one is still looked for. To come: it stops being looked for and is never shared. Keep the file; never delete it. |
| A file deleted | It leaves the catalog, but its stored versions and Observations stay. Archive instead. |
| A new Pattern Type | The tagging step looks for it from the next Conversation end; the tagging prompt grows, so each Conversation end and each Tagging Eval run costs a little more. |
| A broken file | Nothing loads; the backend starts on the last catalog and prints every problem. |

## Review status

- **draft**: may gather evidence silently; never becomes Ready or shared.
- **approved**: may become Ready and be shared once the gate passes. Set
  `approved_by` (e.g. `Zaf`) and `approved_on` (e.g. `2026-11-25`).
- **archived**: retired. Kept so old Observations still make sense. Until
  that is built, it is still looked for at tagging.

Approving is a change like any other: a new version, a review and a deploy.
