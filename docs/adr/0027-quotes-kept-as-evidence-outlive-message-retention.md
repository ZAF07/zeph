# Quotes kept as evidence outlive Message Retention

Status: accepted. Built: Observations (issue 11), the "Things you said" list and telling Users first (issue 13).

Message Retention deletes a User's raw messages after an Admin-set number of days (30 today). A Pattern's evidence builds over months and must rest on the User's exact words, which code checks against the message. So each Observation keeps its quote, a short span and never the whole message, as User Memory, along with a line on what was going on, written by the model and shown apart from the quote.

## Considered Options

- **Paraphrase once the message is deleted.** Rejected: it loses the word-for-word check, and a paraphrase is the model's reading, not the User's words.
- **Longer Message Retention.** Rejected: it keeps everything to save a few lines.

## Consequences

- Users see every kept quote under "Things you said that Zeph kept", with its line and day and no Pattern named, and can delete it; its Pattern is scored again at once. This holds even while the Pattern itself is hidden.
- Delete My Data and Account Deletion remove all Observations. With User Memory off, none are made.
- Admins never see quotes, only counts.
- Users are told plainly, wherever Message Retention is explained, that quotes kept as evidence stay until they delete them. Existing Users are told before Pattern noticing starts for them. They are told on the Dashboard (Home and Memories), with a "Got it" button, and no quote is kept for a User until they press it; the same rule holds for new Users (owner, issue 13).
