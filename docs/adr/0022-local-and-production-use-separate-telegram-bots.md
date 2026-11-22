# Local and production use separate Telegram bots

A Telegram bot has one webhook, and the backend points it at itself on every start (ADR-0005). Once production runs, a shared bot would move between production and the local ngrok tunnel whenever either stack started, and Users' messages would land on a laptop. Production keeps the real bot; local development and worktrees use a second bot with its own token, set only in the local `.env`. Until that bot exists, the local `.env` sets `TELEGRAM_WEBHOOK_REGISTER=false` so production keeps the webhook.

## Considered Options

- **One bot, local registration turned off for good.** No second bot to manage, but the local stack would never get real Telegram messages, and the webhook path ADR-0005 wants tested locally would go untested.
- **One bot, polling locally.** Rejected in ADR-0005: the local path would differ from production.

## Consequences

- A Telegram link stores the User's Telegram chat, which is the same for every bot, so a database copied between local and production keeps working. Each User must press Start on a bot once before it can message them.
- A copied database brings its Telegram links with it, so both stacks can send that User Check-ins, each from its own bot.
- Steps are in `docs/LOCAL_TELEGRAM_BOT_GUIDE.md`.
