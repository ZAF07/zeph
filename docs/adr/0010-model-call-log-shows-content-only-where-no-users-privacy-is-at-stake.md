# The Model Call Log shows content only where no User's privacy is at stake

Every model call is recorded in a Model Call Log that Admins see on the Dashboard, at two levels. For every User it holds no content: the steps, models, tokens, timings, errors and the shape of each decision (e.g. which Need, how many Life Threads were found). Full content (instructions, history, tools, tool calls and results, the response and the model's reasoning) is kept only for Admins' own chats, Eval runs and local or worktree runs. We chose this because the product promises that Admins never see what Users say (Check-in Log, Safeguard Event and Usage hold no message text), and a full prompt holds a User's Conversation, User Portrait, Life Threads and Curiosities.

## Considered options

- **Full content for everyone, kept briefly, with access logged.** Rejected: better for debugging one User's bad reply, but it breaks the promise. If it is ever wanted, it should be the User's choice to share a Conversation.

## Consequences

- Message Retention, Delete My Data and Account Deletion remove a User's log entries, like their messages.
- Debugging a real User's bad reply means reproducing it in an Admin's own chat or in an Eval, not reading theirs.
