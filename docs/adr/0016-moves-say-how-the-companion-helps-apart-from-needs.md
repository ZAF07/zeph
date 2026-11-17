# Moves say how the Companion helps, apart from Needs

The Companion kept missing chances to help: in a real chat about finding app hosting, every Message was read as Accountability, whose "how to reply" only asks for the next step, so Zeph handed the work back five times instead of looking up options. We split "what the User wants" (the Need) from "what the Companion does about it" (the Move): the Understanding picks a Need, then a lead Move and at most one supporting Move from those the Need allows, and may hold a next Move in mind. Each Move's result is kept per User as a Move Outcome, with the situation and mood it happened in. We chose this over only rewriting the Needs' wording because help written into each Need's text can't be counted, learned from, gated by plan or reused, and learning what helps each User, in which situation and mood, is the point of Zeph.

## Considered Options

- **Rewrite Needs, Persona and tool wording only.** Cheapest and Admin-editable, but "how Zeph helps" stays buried in prose: no per-User learning, no Feature-gated help, no Eval of the help separate from the read of the User.
- **Moves replace Needs.** Leaner, but loses what the User wants, which is what stops the Companion helping when it shouldn't (no Push while venting).
- **Several equal Moves per reply, or a full plan up front.** More human on paper, but how the User took a reply can't be credited to one Move, and a fixed plan fights real conversation.

## Consequences

- Needs keep tone and stance and list the Moves that never go with them; Moves are Admin-managed data (ADR-0004), like Needs.
- A Move may need a Feature (Research needs Web Search); when that Feature doesn't work for the User, or its daily limit is used up, the Move is never offered, so plan tiers apply to help the same way they apply to tools.
- Move Outcomes are User Memory: kept when a Conversation ends, found by closeness to the current situation and mood, seen and deleted by the User, feeding the User Portrait.
- A next Move left unmade carries over only through Curiosities, so it comes back the way a friend's follow-up would, not as a stale plan.
- The Understanding Eval checks Moves, and a Move Outcome Eval checks what is learned.
