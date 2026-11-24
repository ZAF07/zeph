# Pattern Types live in git, not in Admin-managed data

Status: accepted, not built yet. An exception to ADR-0004.

ADR-0004 keeps everything that shapes the Companion as data Admins edit on the Dashboard, live from the next reply. Pattern Types are the exception: they are YAML files in the repo, loaded into the database on deploy, and Admins can read them on the Dashboard but not edit them. A Pattern Type decides what Zeph may claim about a person, and every Observation is tagged under one version of it. A live edit would change the meaning of evidence already gathered with no way to score it again, and would reach Users with no review and no Eval run.

## Considered Options

- **Admin-editable like Moves and Needs.** Rejected for now, for the reasons above.
- **Dashboard editing with drafts** (edit a draft, run the Eval on it, Make Live, every version kept). The right end state, and most of it exists as Eval Variants and Make Live. Deferred until the catalog has stopped changing shape.

## Consequences

- Changing a Pattern Type needs a deploy. That is meant: it should be slow and reviewed.
- Each Pattern Type is draft, approved or archived; only approved ones can become ready.
- Numbers that apply to every Pattern Type (score bars, situations needed, fading, limits) are Platform Settings as usual, with hints, and can be overridden in an Eval Variant. Prompts stay Admin-editable and hold no numbers.
- Thought Experiments are Admin-managed data on the Dashboard: a bad edit costs one awkward question and changes no past evidence.
- An Admin guide in `docs/pattern-catalog/README.md` says how to change a Pattern Type and what each change does.
- A model suggesting Pattern Types from the unmatched review list, saved into the YAML by the backend, is parked for its own PRD (`.scratch/pattern-pipeline/grill-decisions.md`).
