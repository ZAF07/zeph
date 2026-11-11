# Users manage settings in chat through LLM tools, not commands

Users can change their settings by talking to the Companion in plain words ("give me a week off", "forget what I said about Jo"), not just on the Dashboard. Response composition gets tools that call core services to make the change; there are no Telegram slash commands besides `/start <token>`. We chose this because the Companion lives in Telegram, and making Users leave the chat to pause a Check-in breaks the feeling of talking to a friend.

## Consequences

- Allowed in chat: pause or resume Check-ins, change Check-in frequency and quiet hours, turn User Memory on or off, forget a specific Memory Item, change time zone, and "Delete my data".
- "Delete my data" in chat only runs after the User replies with an exact confirmation word; anything else cancels it.
- Dashboard only: Delete account, country, and disconnecting Telegram — permanent or safety-related, so a misread message must not trigger them.
- The tools call the same core services as the Dashboard API, so both show one state; each change is recorded as made via chat.
- The Companion says plainly what it changed in its reply. The Safeguard still runs first, so a crisis message never triggers a tool.
