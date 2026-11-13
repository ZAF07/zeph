from dataclasses import asdict
from typing import Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from companion.core.conversations import ConversationServices
from companion.core.models import (
    ChannelPhoto,
    ConversationTurn,
    MessageKind,
    RiskType,
)
from companion.core.user_data import DataDeletionAnswer


class TurnState(TypedDict, total=False):
    """What the graph knows while answering one message.

    IDs are stored as strings so checkpoints stay plain JSON-like data.
    Every turn sets `sticker_id`, "" for none, so a sticker from an earlier
    turn on the same thread is never sent again. Every turn past the
    Safeguard sets `data_deletion_answer` too, for the same reason.
    """

    user_id: str
    chat_id: int
    text: str
    kind: str
    photos: list[dict[str, Any]]
    conversation_id: str
    risk_type: str
    data_deletion_answer: str
    within_message_limit: bool
    memory: str
    knowledge: str
    reply_parts: list[str]
    sticker_id: str


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
    one checkpoint thread, keyed by their User ID. Every value a step reads is
    set earlier in the same turn, so a thread carries nothing from one message
    to the next and can be deleted between messages.
    """

    def __init__(
        self, services: ConversationServices, checkpointer: PostgresSaver
    ) -> None:
        """Build the graph.

        Args:
            services: The core services each step calls.
            checkpointer: Saves the graph's state after each step.
        """
        self._checkpointer = checkpointer

        def record_incoming(state: TurnState) -> TurnState:
            """Save the User's message into their open Conversation.

            Args:
                state: The graph's state so far.

            Returns:
                The ID of that Conversation.
            """
            conversation_id = services.conversations.record_incoming(
                UUID(state["user_id"]),
                state["chat_id"],
                state["text"],
                MessageKind(state["kind"]),
                tuple(ChannelPhoto(**photo) for photo in state["photos"]),
            )
            return {"conversation_id": str(conversation_id)}

        def check_safeguard(state: TurnState) -> TurnState:
            """Check the User's message for crisis.

            Args:
                state: The graph's state so far.

            Returns:
                The risk type the Safeguard saw.
            """
            risk_type = services.safeguard.assess(
                UUID(state["conversation_id"]), UUID(state["user_id"])
            )
            return {"risk_type": risk_type.value}

        def after_safeguard(state: TurnState) -> str:
            """Pick the next step: the Crisis Reply, or settling a data deletion.

            Args:
                state: The graph's state so far.

            Returns:
                The name of the next step.
            """
            if state["risk_type"] == RiskType.NONE.value:
                return "settle_data_deletion"
            return "send_crisis_reply"

        def settle_data_deletion(state: TurnState) -> TurnState:
            """Delete the User's data if this message confirms they asked to.

            Any other message cancels the request.

            Args:
                state: The graph's state so far.

            Returns:
                What the message did to a request to delete their data.
            """
            answer = services.data_deletion.settle(
                UUID(state["user_id"]), state["chat_id"], state["text"]
            )
            return {"data_deletion_answer": answer.value}

        def after_data_deletion(state: TurnState) -> str:
            """Pick the next step: stop once the data is deleted, or go on.

            Args:
                state: The graph's state so far.

            Returns:
                The name of the next step.
            """
            if state["data_deletion_answer"] == DataDeletionAnswer.CONFIRMED.value:
                return END
            return "check_message_limit"

        def check_message_limit(state: TurnState) -> TurnState:
            """Count the message toward the User's daily message limit.

            Args:
                state: The graph's state so far.

            Returns:
                Whether the message is within the limit.
            """
            within_limit = services.usage_limiter.claim_message(UUID(state["user_id"]))
            return {"within_message_limit": within_limit}

        def after_message_limit(state: TurnState) -> str:
            """Pick the next step: a normal reply, or the limit reply.

            Args:
                state: The graph's state so far.

            Returns:
                The name of the next step.
            """
            if state["within_message_limit"]:
                return "recall_memory"
            return "send_limit_reply"

        def send_limit_reply(state: TurnState) -> TurnState:
            """Send the in-character limit reply instead of composing one.

            Args:
                state: The graph's state so far.

            Returns:
                Nothing new to add to the state.
            """
            services.conversations.deliver_at_once(
                UUID(state["conversation_id"]),
                state["chat_id"],
                services.usage_limiter.limit_reply(),
            )
            return {}

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

        def cancel_data_deletion(state: TurnState) -> TurnState:
            """Cancel a request to delete the User's data after a crisis message.

            Args:
                state: The graph's state so far.

            Returns:
                Whether a request was cancelled.
            """
            answer = services.data_deletion.cancel(UUID(state["user_id"]))
            return {"data_deletion_answer": answer.value}

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
                UUID(state["user_id"]), UUID(state["conversation_id"])
            )
            return {"knowledge": knowledge}

        def compose_reply(state: TurnState) -> TurnState:
            """Write the Companion's reply.

            Args:
                state: The graph's state so far.

            Returns:
                The reply as short messages, and its sticker's ID or "".
            """
            reply = services.response_composer.compose(
                UUID(state["conversation_id"]),
                UUID(state["user_id"]),
                state["memory"],
                state["knowledge"],
                data_deletion_cancelled=state["data_deletion_answer"]
                == DataDeletionAnswer.CANCELLED.value,
            )
            sticker_id = str(reply.sticker.id) if reply.sticker else ""
            return {"reply_parts": reply.parts, "sticker_id": sticker_id}

        def deliver_reply(state: TurnState) -> TurnState:
            """Send the reply and save it to the Conversation.

            Args:
                state: The graph's state so far.

            Returns:
                Nothing new to add to the state.
            """
            sticker_id = state["sticker_id"]
            services.conversations.deliver_reply(
                UUID(state["conversation_id"]),
                state["chat_id"],
                state["reply_parts"],
                UUID(sticker_id) if sticker_id else None,
            )
            return {}

        graph = StateGraph(TurnState)
        graph.add_node("record_incoming", record_incoming)
        graph.add_node("check_safeguard", check_safeguard)
        graph.add_node("send_crisis_reply", send_crisis_reply)
        graph.add_node("cancel_data_deletion", cancel_data_deletion)
        graph.add_node("settle_data_deletion", settle_data_deletion)
        graph.add_node("check_message_limit", check_message_limit)
        graph.add_node("send_limit_reply", send_limit_reply)
        graph.add_node("recall_memory", recall_memory)
        graph.add_node("recall_knowledge", recall_knowledge)
        graph.add_node("compose_reply", compose_reply)
        graph.add_node("deliver_reply", deliver_reply)
        graph.add_edge(START, "record_incoming")
        graph.add_edge("record_incoming", "check_safeguard")
        graph.add_conditional_edges(
            "check_safeguard",
            after_safeguard,
            ["send_crisis_reply", "settle_data_deletion"],
        )
        graph.add_edge("send_crisis_reply", "cancel_data_deletion")
        graph.add_edge("cancel_data_deletion", END)
        graph.add_conditional_edges(
            "settle_data_deletion",
            after_data_deletion,
            ["check_message_limit", END],
        )
        graph.add_conditional_edges(
            "check_message_limit",
            after_message_limit,
            ["recall_memory", "send_limit_reply"],
        )
        graph.add_edge("send_limit_reply", END)
        graph.add_edge("recall_memory", "recall_knowledge")
        graph.add_edge("recall_knowledge", "compose_reply")
        graph.add_edge("compose_reply", "deliver_reply")
        graph.add_edge("deliver_reply", END)
        self._graph = graph.compile(checkpointer=checkpointer)

    def handle(self, turn: ConversationTurn) -> None:
        """Answer one message: save it, run the Safeguard, then reply.

        On a crisis the Crisis Reply is sent instead of a composed reply, and
        the message doesn't count toward the daily message limit, and cancels
        any request to delete the User's data. Otherwise a pending request is
        settled first: the confirmation word deletes their data, and then
        their checkpoint thread too, with nothing composed. Over the limit,
        the in-character limit reply is sent and nothing is composed.
        Otherwise the User Memory that matters and the Knowledge that may fit
        are recalled for the reply.

        Args:
            turn: The message to answer.
        """
        final_state = self._graph.invoke(
            {
                "user_id": str(turn.user_id),
                "chat_id": turn.chat_id,
                "text": turn.text,
                "kind": turn.kind.value,
                "photos": [asdict(photo) for photo in turn.photos],
            },
            config={"configurable": {"thread_id": str(turn.user_id)}},
        )
        if final_state.get("data_deletion_answer") == DataDeletionAnswer.CONFIRMED:
            self.forget_user(turn.user_id)

    def forget_user(self, user_id: UUID) -> None:
        """Delete the User's checkpoint thread, which holds copies of their messages.

        Args:
            user_id: The User's ID.
        """
        self._checkpointer.delete_thread(str(user_id))
