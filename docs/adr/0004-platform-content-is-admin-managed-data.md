# Platform content and settings are admin-managed data, not code

Nothing about how the Companion behaves is hardcoded: prompts and persona, Crisis Reply wording, Helplines, Knowledge, Memory Categories and tunable settings (e.g. Conversation quiet gap) live in the database and are managed from the Dashboard's admin area. Initial values are loaded from seed data files, never written into code. We chose this because the MVP is built as the real product, and these things will change per country and over time without a redeploy.

## Consequences

- Memory Categories can be added, renamed and archived but never deleted, so existing Memory Items always keep a valid category.
- Every core service reads its settings at runtime rather than at import time.
- The exceptions live in `.env` and need a restart: secrets, which adapter backs each port, and the initial Admin emails. Secrets never enter the database, so the admin area cannot expose them.
- The model used by each core service (e.g. a cheaper one for the Safeguard) is an admin setting, not a code constant.
