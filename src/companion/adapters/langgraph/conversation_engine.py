from typing import Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from companion.core.conversations import ConversationServices
from companion.core.models import ConversationTurn


class TurnState(TypedDict, total=False):
    """What the graph knows while answering one message.

    IDs are stored as strings so checkpoints stay plain JSON-like data.
    """

    user_id: str
    chat_id: int
    text: str
    conversation_id: str
    reply_parts: list[str]


def build_postgres_checkpointer(database_url: str) -> PostgresSaver:
    """Connect LangGraph's checkpointer to Postgres and create its tables.

    Args:
        database_url: SQLAlchemy URL of the database
            (`postgresql+psycopg://...`).

    Returns:
        The checkpointer, backed by a small connection pool.
    """
    pool: ConnectionPool[Any] = ConnectionPool(
        database_url.replace("postgresql+psycopg://", "postgresql://"),
        min_size=1,
        max_size=5,
        open=True,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return checkpointer


class LangGraphConversationEngine:
    """Answers a message by running the core services as LangGraph steps.

    Each step is a thin call into a core service (ADR-0003). Every User has
    one checkpoint thread, keyed by their User ID.
    """

    def __init__(
        self, services: ConversationServices, checkpointer: PostgresSaver
    ) -> None:
        """Build the graph.

        Args:
            services: The core services each step calls.
            checkpointer: Saves the graph's state after each step.
        """

        def record_incoming(state: TurnState) -> TurnState:
            """Save the User's message into their open Conversation.

            Args:
                state: The graph's state so far.

            Returns:
                The ID of that Conversation.
            """
            conversation_id = services.conversations.record_incoming(
                UUID(state["user_id"]), state["chat_id"], state["text"]
            )
            return {"conversation_id": str(conversation_id)}

        def compose_reply(state: TurnState) -> TurnState:
            """Write the Companion's reply.

            Args:
                state: The graph's state so far.

            Returns:
                The reply as short messages.
            """
            reply_parts = services.response_composer.compose(
                UUID(state["conversation_id"])
            )
            return {"reply_parts": reply_parts}

        def deliver_reply(state: TurnState) -> TurnState:
            """Send the reply and save it to the Conversation.

            Args:
                state: The graph's state so far.

            Returns:
                Nothing new to add to the state.
            """
            services.conversations.deliver_reply(
                UUID(state["conversation_id"]), state["chat_id"], state["reply_parts"]
            )
            return {}

        graph = StateGraph(TurnState)
        graph.add_node("record_incoming", record_incoming)
        graph.add_node("compose_reply", compose_reply)
        graph.add_node("deliver_reply", deliver_reply)
        graph.add_edge(START, "record_incoming")
        graph.add_edge("record_incoming", "compose_reply")
        graph.add_edge("compose_reply", "deliver_reply")
        graph.add_edge("deliver_reply", END)
        self._graph = graph.compile(checkpointer=checkpointer)

    def handle(self, turn: ConversationTurn) -> None:
        """Answer one message: save it, compose a reply and send it.

        Args:
            turn: The message to answer.
        """
        self._graph.invoke(
            {
                "user_id": str(turn.user_id),
                "chat_id": turn.chat_id,
                "text": turn.text,
            },
            config={"configurable": {"thread_id": str(turn.user_id)}},
        )
