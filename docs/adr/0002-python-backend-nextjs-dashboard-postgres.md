# Python backend, Next.js dashboard, Postgres

The backend (Telegram webhook, Dashboard API, check-in scheduler) is a single Python FastAPI service; the Dashboard is a separate Next.js (TypeScript) app in `web/`; both use Postgres. We accept two languages because Clerk's support is strongest in Next.js, while the AI, memory and conversation logic stays in Python.
