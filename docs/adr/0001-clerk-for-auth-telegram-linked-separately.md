# Clerk for dashboard auth, Telegram linked separately

Users sign in to the Dashboard through Clerk, and connect their Telegram account afterwards with a one-time link from the Dashboard. We chose this over "Log in with Telegram" so account identity is not tied to a single chat channel and we get standard auth (email, social, sessions) without building it ourselves.

## Consequences

- A User can exist without a Telegram connection; the Companion is unreachable for them until they connect.
- Clerk's user ID is the account identity; the Telegram user ID is an attribute of the User, not the key.
- The Clerk secret key is shared by the backend and the Dashboard's server, because Clerk's Next.js middleware needs it. It is never sent to the browser. Every other secret (database, Telegram, LLM, search) stays backend-only.
