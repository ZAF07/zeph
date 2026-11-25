# Migrations

Alembic migrations live in `versions/`, numbered in order. They run when the backend starts (`companion.prestart`), before the seed files load.

## Changing a seed prompt

A prompt in `src/companion/seed/platform_settings.yaml` loads only where it isn't stored yet. So when you change a seed prompt, a migration has to remove the stored one for the new text to load.

**A new migration must use the helper `reload_prompt_unless_edited` for this. Never delete a prompt from `platform_settings` yourself.** A plain delete also throws away an Admin's edit from the Dashboard, and nothing says so.

The helper removes the stored prompt only when it still equals the seed text you are replacing. If an Admin edited it, the edit stays and a warning naming the setting goes to the backend log, so the owner can merge the new seed text by hand.

1. Get the hash of the seed text you are replacing (the one on `main`; a second argument names another git ref):

   ```
   uv run python -m scripts.seed_prompt_hash pattern_tagging_prompt
   ```

2. Write the whole hash out in the migration (it is cut short below; the helper refuses anything that isn't a full hash) and call the helper:

   ```python
   from alembic import op

   from companion.adapters.postgres.prompt_reload import reload_prompt_unless_edited

   PREVIOUS_SEED_HASHES = {
       "pattern_tagging_prompt": "1b761f35…",
   }


   def upgrade() -> None:
       """Reload the tagging prompt where no Admin edited it."""
       for key, previous_seed_hash in PREVIOUS_SEED_HASHES.items():
           reload_prompt_unless_edited(op.get_bind(), key, previous_seed_hash)
   ```

The hash is written out in the migration, so later seed changes don't change what the migration does.

The warning is printed once, in the backend log of the deploy that runs the migration (`docker compose logs backend | grep "Kept the stored"`). Check for it after a deploy that changes a prompt.

A stored prompt that already differs from the previous seed for any reason (an Admin's edit, or an older seed text that was never reloaded) counts as edited and is kept.

Migrations 0073, 0078, 0080, 0081, 0086, 0100 and 0101 removed prompts without this check. They have already run on production and stay as they are.
