from dataclasses import asdict
from typing import Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from companion.core.conversation_services import ConversationServices
from companion.core.models import (
    ChannelPhoto,
    ChannelSticker,
    MessageKind,
    MessageToAnswer,
    UserSnapshot,
)
from companion.core.reply_gate import Stopped, StopReason


class ReplyState(TypedDict, total=False):
    """What the graph knows while answering one message.

    IDs are stored as strings so checkpoints stay plain JSON-like data.
    Every message sets `stop_reason`, "" when a reply is needed, and every
    composed reply sets `sticker_id` and `shared_photo_id`, "" for none, so a
    value from an earlier message on the same thread is never used again.
    """

    user_id: str
    chat_id: int
    text: str
    kind: str
    photos: list[dict[str, Any]]
    sticker: dict[str, Any] | None
    safeguard_text: str
    stop_reason: str
    conversation_id: str
    data_deletion_cancelled: bool
    memory: str
    shared_photo_ids: list[str]
    knowledge: str
    reply_parts: list[str]
    sticker_id: str
    shared_photo_id: str


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

    The first step asks the core ReplyGate whether a reply is needed; the
    rest recall memory and Knowledge, compose the reply and deliver it. Each
    step is a thin call into a core service (ADR-0003). The User snapshot is
    the run's context, so every step reads the same User and is never saved
    in a checkpoint. Every User has
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

        def check(state: ReplyState, runtime: Runtime[UserSnapshot]) -> ReplyState:
            """Save the User's message and apply the house rules.

            Args:
                state: The graph's state so far.
                runtime: Holds the User snapshot.

            Returns:
                Why no reply is composed, or "" with the Conversation's ID and
                whether a Delete My Data was cancelled.
            """
            sticker = state.get("sticker")
            result = services.reply_gate.check(
                MessageToAnswer(
                    user_id=UUID(state["user_id"]),
                    chat_id=state["chat_id"],
                    text=state["text"],
                    kind=MessageKind(state["kind"]),
                    photos=tuple(ChannelPhoto(**photo) for photo in state["photos"]),
                    safeguard_text=state["safeguard_text"] or None,
                    sticker=ChannelSticker(**sticker) if sticker else None,
                ),
                runtime.context,
            )
            if isinstance(result, Stopped):
                return {"stop_reason": result.reason.value}
            return {
                "stop_reason": "",
                "conversation_id": str(result.conversation_id),
                "data_deletion_cancelled": result.data_deletion_cancelled,
            }

        def after_check(state: ReplyState) -> str:
            """Pick the next step: compose a reply only if one is needed.

            Args:
                state: The graph's state so far.

            Returns:
                The name of the next step.
            """
            if state["stop_reason"]:
                return END
            return "recall_memory"

        def recall_memory(
            state: ReplyState, runtime: Runtime[UserSnapshot]
        ) -> ReplyState:
            """Find the User Memory that matters for the message.

            Args:
                state: The graph's state so far.
                runtime: Holds the User snapshot.

            Returns:
                The memory to give the reply, and the IDs of the Shared
                Photos that matter.
            """
            recalled = services.memory_retrieval.recall(
                runtime.context, UUID(state["conversation_id"])
            )
            return {
                "memory": recalled.text,
                "shared_photo_ids": [
                    str(photo_id) for photo_id in recalled.shared_photo_ids
                ],
            }

        def recall_knowledge(
            state: ReplyState, runtime: Runtime[UserSnapshot]
        ) -> ReplyState:
            """Find the Knowledge that may fit the message.

            Args:
                state: The graph's state so far.
                runtime: Holds the User snapshot.

            Returns:
                The Knowledge to give the reply.
            """
            knowledge = services.knowledge_retrieval.recall(
                runtime.context, UUID(state["conversation_id"])
            )
            return {"knowledge": knowledge}

        def compose_reply(
            state: ReplyState, runtime: Runtime[UserSnapshot]
        ) -> ReplyState:
            """Write the Companion's reply.

            Args:
                state: The graph's state so far.
                runtime: Holds the User snapshot.

            Returns:
                The reply as short messages, and its sticker's and Shared
                Photo's IDs, or "".
            """
            reply = services.response_composer.compose(
                UUID(state["conversation_id"]),
                runtime.context,
                state["memory"],
                state["knowledge"],
                data_deletion_cancelled=state["data_deletion_cancelled"],
                shared_photo_ids=[
                    UUID(photo_id) for photo_id in state["shared_photo_ids"]
                ],
            )
            sticker_id = str(reply.sticker.id) if reply.sticker else ""
            shared_photo_id = str(reply.shared_photo.id) if reply.shared_photo else ""
            return {
                "reply_parts": reply.parts,
                "sticker_id": sticker_id,
                "shared_photo_id": shared_photo_id,
            }

        def deliver_reply(state: ReplyState) -> ReplyState:
            """Send the reply and save it to the Conversation.

            Args:
                state: The graph's state so far.

            Returns:
                Nothing new to add to the state.
            """
            sticker_id = state["sticker_id"]
            shared_photo_id = state["shared_photo_id"]
            services.conversations.deliver_reply(
                UUID(state["user_id"]),
                UUID(state["conversation_id"]),
                state["chat_id"],
                state["reply_parts"],
                UUID(sticker_id) if sticker_id else None,
                UUID(shared_photo_id) if shared_photo_id else None,
            )
            return {}

        graph = StateGraph(ReplyState, context_schema=UserSnapshot)
        graph.add_node("check", check)
        graph.add_node("recall_memory", recall_memory)
        graph.add_node("recall_knowledge", recall_knowledge)
        graph.add_node("compose_reply", compose_reply)
        graph.add_node("deliver_reply", deliver_reply)
        graph.add_edge(START, "check")
        graph.add_conditional_edges("check", after_check, ["recall_memory", END])
        graph.add_edge("recall_memory", "recall_knowledge")
        graph.add_edge("recall_knowledge", "compose_reply")
        graph.add_edge("compose_reply", "deliver_reply")
        graph.add_edge("deliver_reply", END)
        self._graph = graph.compile(checkpointer=checkpointer)

    def handle(self, message: MessageToAnswer, user: UserSnapshot) -> None:
        """Answer one message: apply the house rules, then reply if needed.

        The ReplyGate saves the message and applies the house rules. When it
        stops the reply nothing is composed; once the User's data is deleted
        their checkpoint thread is deleted too. Otherwise the User Memory that
        matters and the Knowledge that may fit are recalled for the reply.

        Args:
            message: The message to answer.
            user: The User who sent it, read once as the reply starts.
        """
        final_state = self._graph.invoke(
            {
                "user_id": str(message.user_id),
                "chat_id": message.chat_id,
                "text": message.text,
                "kind": message.kind.value,
                "photos": [asdict(photo) for photo in message.photos],
                "sticker": asdict(message.sticker) if message.sticker else None,
                "safeguard_text": message.safeguard_text or "",
            },
            config={"configurable": {"thread_id": str(message.user_id)}},
            context=user,
        )
        if final_state["stop_reason"] == StopReason.DATA_DELETED:
            self.forget_user(message.user_id)

    def forget_user(self, user_id: UUID) -> None:
        """Delete the User's checkpoint thread, which holds copies of their messages.

        Args:
            user_id: The User's ID.
        """
        self._checkpointer.delete_thread(str(user_id))
