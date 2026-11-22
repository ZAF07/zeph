# Local and production Telegram bots

## Why two bots

Telegram sends a bot's messages to one address only (its webhook). Every time the backend starts, it points the webhook at itself, using `WEBHOOK_BASE_URL`. Production points it at `https://<domain>`, the local stack at its ngrok address, and whichever starts last wins.

With one bot shared by both stacks, starting the local stack would move the bot's messages from production to your laptop. So production keeps the real bot, and local development uses its own bot (ADR-0022).

## Until the local bot exists

The local `.env` has:

```
TELEGRAM_WEBHOOK_REGISTER=false
```

The local backend then leaves the webhook alone, so it stays with production. The local stack gets no real Telegram messages in this state. Test it by posting updates to `http://localhost:8000/telegram/webhook`, as worktrees do. It can still send messages with the shared token, so local Check-ins may still reach you.

## Set up the local bot

1. **Make the bot.** In Telegram, open @BotFather, send `/newbot` and follow the steps. Pick a name that says it's for development, for example `zeph_dev_bot`. BotFather replies with its token.
2. **Update the local `.env`** (the main folder only, never the server's):

   ```
   TELEGRAM_BOT_TOKEN=<the new bot's token>
   TELEGRAM_BOT_USERNAME=zeph_dev_bot
   ```

   Delete the `TELEGRAM_WEBHOOK_REGISTER=false` line, so the local backend registers its own bot's webhook again.

3. **Restart:** `make restart`.
4. **Start the bot.** Open the new bot in Telegram and press **Start**. A bot can't message you until you have. Your Telegram link carries over: it stores your Telegram chat, which is the same for every bot, so there is no need to connect again.

Check: send the local bot a message and Zeph replies. `docker compose logs backend` shows `Telegram webhook registered at https://<NGROK_DOMAIN>/telegram/webhook`.

Worktrees copy the main `.env`, so they use the local bot too, and keep `TELEGRAM_WEBHOOK_REGISTER=false` so the main local stack owns it.
