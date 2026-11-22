# 37 — Separate Telegram bot for local development

Status: ready-for-human

## Parent

`.scratch/mvp/PRD.md`

## What to do

Give the local stack its own Telegram bot, so it never takes the production bot's webhook (ADR-0022). Follow `docs/LOCAL_TELEGRAM_BOT_GUIDE.md` ("Set up the local bot").

Until then, the local `.env` has `TELEGRAM_WEBHOOK_REGISTER=false` (set 2026-11-22), so production keeps the real bot.

## Acceptance criteria

- [ ] A second bot exists in BotFather, named as a development bot
- [ ] The local `.env` has the new bot's token and username, and no `TELEGRAM_WEBHOOK_REGISTER=false`
- [ ] After `make restart`, the backend logs show the webhook registered at the ngrok address
- [ ] A message to the local bot gets a reply from local Zeph, and production's `getWebhookInfo` still shows the production domain

## Blocked by

None
