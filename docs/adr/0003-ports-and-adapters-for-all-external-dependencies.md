# Ports and adapters for every external dependency

Every external dependency — LLM provider, conversation framework, auth, database, vector store, embeddings, web search, scheduler and chat channel — sits behind a port in the core, with the concrete adapter chosen via config. For the MVP the adapters are DeepSeek (via LangChain's chat-model interface), LangGraph, Clerk, Postgres, pgvector, a local fastembed model, Tavily, an in-process scheduler loop and Telegram. LangGraph lives inside an adapter rather than the core, so the core never imports LangChain or LangGraph.

## Consequences

- Swapping Clerk is cheap on the backend (token verification port) but not in the Next.js Dashboard, which uses Clerk's UI components directly.
- LangGraph orchestrates the core services (step order, branching, checkpointing), but each graph node is a thin call into a core service. Business logic lives in the services, never in the graph, so replacing LangGraph means rewriting only the wiring.
- LangGraph's Postgres checkpointer belongs to the LangGraph adapter, not to the core's persistence port.
