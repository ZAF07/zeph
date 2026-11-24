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

All fifteen start as draft. The owner reads each one and approves it or sends
it back.

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
| `status` | draft, approved or archived. See "Review status" below. | The Dashboard. Sharing will read it (not built yet). |
| `approved_by`, `approved_on` | Who approved it and on what day. Both or neither; only for approved or archived. | The Dashboard. |
| `definition` | What the Pattern is, in two or three sentences, including what it is *not*. | The tagging model. |
| `if`, `then`, `function` | The situation, the behaviour, and what it does for the person. | The tagging model; the Dashboard card title. |
| `frameworks` | Published ideas the Pattern Type draws on. For the owner and a future reviewer only. | The Dashboard. Never sent to a model or shown to a User. |
| `signs` | What counts **for** it. Each has an `id` (I1, I2…), `text`, `strength` (weak, moderate, strong) and `part` (situation, inside, behaviour). | The tagging model picks one per Observation; scoring turns its strength into points. |
| `signs_against` | What counts **against** it. Same fields, IDs D1, D2…. | Same as signs; against Observations take points away. |
| `look_alikes` | What it can be mistaken for. Either another `pattern_type` (by ID) or a `name` for something outside the catalog (e.g. healthy focus), with `tells_apart`. | The tagging model: when it can't tell two look-alikes apart it names both, and the Observation is unclear. |
| `anyone_would` | When anyone would act this way, so it says nothing about the person. | The tagging model. |
| `anyone_would_when` | Optional. The same, as situation tags: `relationship`, `power`, `setting`, `stance`. A match needs every tag it names. | Code: an Observation whose tags fit is situational and carries no weight. |
| `exclusions` | When it must not be shared, and whether evidence from then is `ignored` or `counted_not_shared`. | Not read yet: the tagging step's exclusion flag and the Ready gate are still to come. |
| `approved_wording` | The Pattern in warm, plain words, as Zeph's view. | Not read yet: sharing (issue 08). |
| `prediction_wording` | One thing to notice next time, with a `{placeholder}` the model fills. | Not read yet: sharing (issue 08). |
| `numbers.situations_needed` | Situations (Life Threads) needed before it can be Ready. | Not read yet: the Ready gate (issue 07). The global Platform Settings apply until then. |
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

## How to add a Pattern Type

Copy a file in the same area and change everything. Pick an ID in the same
shape (`AREA.DRIVER.BEHAVIOUR`), set `version: 0.1.0` and `status: draft`. Add
it as a look-alike to every Pattern Type it can be mistaken for, with new
versions for those. Add at least one Tagging Eval case for it and one against
it (a test needs both for every Pattern Type). Then follow steps 4 to 6 above.

When a Pattern Type is added, old unmatched evidence is to be tagged again
against it (issue 16, not built yet).

## What each change does

| Change | What happens |
|---|---|
| New version of any field | Loaded on the next start. Older versions stay stored; Observations keep the version they were tagged under. |
| A sign's `strength` | Scores shift on the next scoring (each Conversation end, or when evidence is deleted): scoring reads the strength from the current version, also for Observations tagged under an older one. |
| A sign removed or its `id` changed | Observations that named it count nothing from the next scoring. The tagging step can't pick it any more. |
| `definition`, `if` / `then` / `function`, signs' `text`, `look_alikes`, `anyone_would` | Changes what the tagging model looks for, from the next Conversation end. Past Observations are not tagged again. Run the Tagging Eval. |
| `anyone_would_when` | Changes which new Observations are situational. Past ones keep how they were marked. |
| `exclusions`, `approved_wording`, `prediction_wording`, `numbers` | Nothing yet; they wait for the Ready gate and sharing. |
| `status` draft → approved | Nothing yet beyond the Dashboard. Once the Ready gate is built, only approved Pattern Types may become Ready and be shared; drafts gather evidence silently. Needs `approved_by` and `approved_on`. |
| `status` → archived | To come: an archived Pattern Type stops being looked for and is never shared. Keep the file; never delete it. |
| A file deleted | It leaves the catalog, but its stored versions and Observations stay. Archive instead. |
| A new Pattern Type | The tagging step looks for it from the next Conversation end; the tagging prompt grows, so each Conversation end and each Tagging Eval run costs a little more. |
| A broken file | Nothing loads; the backend starts on the last catalog and prints every problem. |

## Review status

- **draft**: may gather evidence silently; never becomes Ready or shared.
- **approved**: may become Ready and be shared once the gate passes. Set
  `approved_by` (e.g. `Zaf`) and `approved_on` (e.g. `2026-11-25`).
- **archived**: retired. Kept so old Observations still make sense.

Approving is a change like any other: a new version, a review and a deploy.
