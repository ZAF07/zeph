from typing import Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from companion.core.conversations import ConversationServices
from companion.core.models import ConversationTurn, RiskType


class TurnState(TypedDict, total=False):
    """What the graph knows while answering one message.

    IDs are stored as strings so checkpoints stay plain JSON-like data.
    """

    user_id: str
    chat_id: int
    text: str
    conversation_id: str
    risk_type: str
    memory: str
    knowledge: str
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

        def check_safeguard(state: TurnState) -> TurnState:
            """Check the User's message for crisis.

            Args:
                state: The graph's state so far.

            Returns:
                The risk type the Safeguard saw.
            """
            risk_type = services.safeguard.assess(UUID(state["conversation_id"]))
            return {"risk_type": risk_type.value}

        def after_safeguard(state: TurnState) -> str:
            """Pick the next step: the Crisis Reply, or a normal reply.

            Args:
                state: The graph's state so far.

            Returns:
                The name of the next step.
            """
            if state["risk_type"] == RiskType.NONE.value:
                return "recall_memory"
            return "send_crisis_reply"

        def send_crisis_reply(state: TurnState) -> TurnState:
            """Send the Crisis Reply and record the Safeguard Event.

            Normal response composition is skipped.

            Args:
                state: The graph's state so far.

            Returns:
                Nothing new to add to the state.
            """
            crisis_reply = services.safeguard.respond_to_crisis(
                UUID(state["user_id"]), RiskType(state["risk_type"])
            )
            services.conversations.deliver_at_once(
                UUID(state["conversation_id"]), state["chat_id"], crisis_reply
            )
            return {}

        def recall_memory(state: TurnState) -> TurnState:
            """Find the User Memory that matters for the message.

            Args:
                state: The graph's state so far.

            Returns:
                The memory to give the reply.
            """
            memory = services.memory_retrieval.recall(
                UUID(state["user_id"]), UUID(state["conversation_id"])
            )
            return {"memory": memory}

        def recall_knowledge(state: TurnState) -> TurnState:
            """Find the Knowledge that may fit the message.

            Args:
                state: The graph's state so far.

            Returns:
                The Knowledge to give the reply.
            """
            knowledge = services.knowledge_retrieval.recall(
                UUID(state["conversation_id"])
            )
            return {"knowledge": knowledge}

        def compose_reply(state: TurnState) -> TurnState:
            """Write the Companion's reply.

            Args:
                state: The graph's state so far.

            Returns:
                The reply as short messages.
            """
            reply_parts = services.response_composer.compose(
                UUID(state["conversation_id"]), state["memory"], state["knowledge"]
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
        graph.add_node("check_safeguard", check_safeguard)
        graph.add_node("send_crisis_reply", send_crisis_reply)
        graph.add_node("recall_memory", recall_memory)
        graph.add_node("recall_knowledge", recall_knowledge)
        graph.add_node("compose_reply", compose_reply)
        graph.add_node("deliver_reply", deliver_reply)
        graph.add_edge(START, "record_incoming")
        graph.add_edge("record_incoming", "check_safeguard")
        graph.add_conditional_edges(
            "check_safeguard",
            after_safeguard,
            ["send_crisis_reply", "recall_memory"],
        )
        graph.add_edge("send_crisis_reply", END)
        graph.add_edge("recall_memory", "recall_knowledge")
        graph.add_edge("recall_knowledge", "compose_reply")
        graph.add_edge("compose_reply", "deliver_reply")
        graph.add_edge("deliver_reply", END)
        self._graph = graph.compile(checkpointer=checkpointer)

    def handle(self, turn: ConversationTurn) -> None:
        """Answer one message: save it, run the Safeguard, then reply.

        On a crisis the Crisis Reply is sent instead of a composed reply.
        Otherwise the User Memory that matters and the Knowledge that may fit
        are recalled for the reply.

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
