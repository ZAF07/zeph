# A migration never drops a prompt an Admin edited

Status: accepted. Built: the helper `reload_prompt_unless_edited` (pattern pipeline issue 28).

Prompts are Platform Settings: Admins edit them on the Dashboard, and the seed loads only where a setting isn't stored yet (ADR 0004). So when a release changes a seed prompt, a migration has to remove the stored one for the new text to load. Seven migrations (0073 to 0101) did this with a plain delete, which also threw away an Admin's edit on deploy, with no sign that it had.

A migration now removes a stored prompt only where it still equals the seed text being replaced. It compares a hash written out in the migration, so it doesn't depend on the seed file as it is today. An edited prompt is kept, and a warning naming the setting goes to the backend log.

## Considered Options

- **Keep the plain delete and tell Admins in release notes.** Rejected: production is live and an edit lost on deploy can't be got back.
- **Always keep the stored prompt and never reload.** Rejected: an install nobody edited would stay on old prompts for ever.
- **Merge the new seed text into the Admin's text in code.** Rejected: prompts are free text, and a wrong merge is worse than none.

## Consequences

- Where an Admin edited a prompt, the new seed text does not load. The step may then read or write something its prompt doesn't cover, until the owner merges the new text by hand. The warning is the only sign, printed once on the deploy that runs the migration.
- A stored prompt that differs from the previous seed for any other reason (an older seed never reloaded) is also kept.
- The seven older migrations stay as they are; they have already run on production.
- How to write such a migration is in `src/companion/adapters/postgres/migrations/README.md`.
