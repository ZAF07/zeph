# Replies are made in small, one-job steps

One Understanding call read the User and decided everything about the reply (Need, Moves, Threads, Curiosities, Knowledge, memory, photos), and a separate Check-in model then added its own order to the reply. In a real Conversation the Understanding wrote "don't reflect it back again, rather than another mirror" and picked Mirror in the same answer, and the Check-in model had the reply weave in a "present-moment pause" just as a rant ended, which the User read as being brushed off. We split the reply path into steps that each do one job: the Understanding (what the User said, means, feels and wants, deciding nothing), Recall (plain code, by meaning), the Reply Plan (Zeph's Read from the Outlook, then the Need, Moves, what the reply uses, and whether a Woven-in Check-in fits), and the Reply. It is still four model calls per reply, as before, including the Safeguard.

## Considered Options

- **Keep one Understanding call, trimmed.** Fewer hops, but reading and deciding still compete in one answer, and Check-ins still need their own call or join the overload.
- **A fast path that skips the Understanding for simple messages.** Cheaper, but short messages ("yep") were the ones that mattered most, and a rule or extra model call can't tell which those are.

## Consequences

- Understanding, Recall and Reply Plan run one after another, so a reply takes longer (about 30 to 40 seconds with the longer wait for the end of a Message). We accept this: a friend reads all your texts before answering.
- The separate Check-in model for Woven-in Check-ins goes; the Reply Plan weighs a due Check-in against everything else. Check-ins sent on their own keep their own decision.
- The Understanding and the Reply Plan get their own Evals, so each job can be checked apart.
- The flow is described in `docs/message-pipeline/README.md`.
