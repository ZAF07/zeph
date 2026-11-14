# Replies run in plain core code, not LangGraph

Status: accepted. Replaces the LangGraph parts of ADR-0003.

A core `ReplyService` runs each reply's steps in plain Python, in a fixed order (house rules → being reminded → Understanding → lookups → reply → deliver). The `ConversationEngine` port, the LangGraph adapter and its Postgres checkpointer are removed. We chose this because the reply is a straight line with no loop or branching that LangGraph helps with, and its checkpoints carry nothing between messages (one User had 1,465 unread checkpoints). The reply's tool loop (web, settings, stickers, photos) already lives in the chat model adapter, not the graph.

## Considered options

- **Keep LangGraph for an Understanding reasoning loop.** Rejected along with letting the reply model drive its own lookups (option B in `.scratch/understanding/`): understanding first, then fetching, keeps speed, cost and behaviour steady.

## Consequences

- If a future hybrid gives the reply a few lookup tools (e.g. search past Conversations), they join the reply call's existing tool loop. That alone is no reason to bring a graph framework back.
- Model-call visibility comes from the Model Call Log (ADR-0010), not from framework tracing.
