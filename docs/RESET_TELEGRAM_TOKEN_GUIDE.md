# Reset the Telegram bot token

The bot token lets anyone who has it read what Users send to Zeph and send messages as Zeph. It never expires, so we only reset it when there is a reason.

## When to reset it

- The token leaked, or might have: in logs, a chat or AI transcript, a screenshot, a ticket, or a commit.
- Someone who had the token no longer should, for example a collaborator left or a server was retired.

There is no regular schedule.

## Before you start

- You need the Telegram account that created the bot in @BotFather.
- You need access to the server's `.env` file and its project folder.
- Do steps 1 to 4 one after another. From step 1 until the restart in step 3 finishes, Zeph can't send any messages.

## Steps

1. **Get a new token.** In Telegram, open @BotFather and send `/mybots`. Pick the bot, then **API Token**, then **Revoke current token**. The old token stops working straight away. BotFather replies with the new token. Copy it.
2. **Put the new token in `.env`.** On the server, open `.env` in the project folder and replace the value:

   ```
   TELEGRAM_BOT_TOKEN=<new token>
   ```

3. **Restart the stack.** In the project folder, run:

   ```
   make restart
   ```

   This rebuilds and recreates the containers so they read the new `.env`. On start, the backend registers the Telegram webhook again with the new token, so there is nothing to do in Telegram. Plain `docker compose restart` does **not** read `.env` again, so don't use it.

4. **Check it works.** Send the bot a message from your own Telegram account and wait for Zeph's reply. If there is no reply, look for errors with:

   ```
   docker compose logs backend --tail 100
   ```

## After

- Update every other copy of `.env` that holds the token, such as other servers or developer worktrees. They stop working with the old token.
- Never paste the token into chats, tickets, AI tools or commits. If that happens, start this guide again.
