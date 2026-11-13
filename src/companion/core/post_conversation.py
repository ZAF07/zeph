import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.features import FeatureService
from companion.core.models import (
    ChatLine,
    ChatRole,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    Feature,
    MemoryCategory,
    MemoryChanges,
    MemoryItem,
    MemorySource,
)
from companion.core.ports import Clock, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

NO_CHANGES = MemoryChanges(added=[], updated=[], removed_ids=[])


@dataclass(frozen=True)
class ProcessingAnswer:
    """What the post-conversation processing model said about a Conversation.

    Attributes:
        summary: What was talked about.
        mood: How the User seemed.
        operations: The add, update and remove operations, as the model
            wrote them; each is checked before it is used.
    """

    summary: str
    mood: str
    operations: list[Any]


@dataclass(frozen=True)
class MemoryChangeContext:
    """What a Conversation's Memory Item operations are checked against.

    Attributes:
        user_id: The User the Memory Items are about.
        conversation_id: The Conversation they were learned in.
        now: When the changes are being made.
        items_by_number: The User's current Memory Items, by the number the
            model was shown for each.
        active_categories: The Memory Categories new items may go in, by
            name in lower case.
    """

    user_id: UUID
    conversation_id: UUID
    now: datetime
    items_by_number: dict[int, MemoryItem]
    active_categories: dict[str, MemoryCategory]


def read_processing_answer(answer: str) -> ProcessingAnswer | None:
    """Read the post-conversation processing model's JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The answer, or None if it has no JSON object with a summary and mood.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    summary, mood = parsed.get("summary"), parsed.get("mood")
    operations = parsed.get("memory_operations", [])
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(mood, str) or not mood.strip():
        return None
    if not isinstance(operations, list):
        operations = []
    return ProcessingAnswer(
        summary=summary.strip(), mood=mood.strip(), operations=operations
    )


def read_text_field(operation: dict[str, Any], key: str) -> str | None:
    """Read a non-empty text field from an operation.

    Args:
        operation: One operation from the model.
        key: The field's name.

    Returns:
        The text without surrounding spaces, or None if it is missing or empty.
    """
    value = operation.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def plan_memory_changes(
    operations: list[Any], context: MemoryChangeContext
) -> MemoryChanges:
    """Turn the model's operations into changes that are safe to save.

    An operation is skipped when it names an unknown item, an archived or
    unknown category, has no content, repeats a fact already remembered, or
    touches an item another operation already changed.

    Args:
        operations: The operations, as the model wrote them.
        context: The User's current Memory Items and the active categories.

    Returns:
        The Memory Items to add, update and remove.
    """
    added: list[MemoryItem] = []
    updated: list[MemoryItem] = []
    removed_ids: list[UUID] = []
    touched_numbers: set[int] = set()
    known_contents = {item.content.lower() for item in context.items_by_number.values()}
    for operation in operations:
        if not isinstance(operation, dict):
            continue
        action = operation.get("action")
        content = read_text_field(operation, "content")
        category_name = (read_text_field(operation, "category") or "").lower()
        category = context.active_categories.get(category_name)
        if action == "add":
            if content is None or category is None:
                continue
            if content.lower() in known_contents:
                continue
            known_contents.add(content.lower())
            added.append(
                MemoryItem(
                    id=uuid4(),
                    user_id=context.user_id,
                    category_id=category.id,
                    content=content,
                    source=MemorySource.CONVERSATION,
                    source_conversation_id=context.conversation_id,
                    created_at=context.now,
                    updated_at=context.now,
                )
            )
            continue
        number = operation.get("item")
        if not isinstance(number, int) or number in touched_numbers:
            continue
        existing = context.items_by_number.get(number)
        if existing is None:
            continue
        if action == "update" and content is not None:
            touched_numbers.add(number)
            updated.append(
                MemoryItem(
                    id=existing.id,
                    user_id=existing.user_id,
                    category_id=category.id if category else existing.category_id,
                    content=content,
                    source=MemorySource.CONVERSATION,
                    source_conversation_id=context.conversation_id,
                    created_at=existing.created_at,
                    updated_at=context.now,
                )
            )
        elif action == "remove":
            touched_numbers.add(number)
            removed_ids.append(existing.id)
    return MemoryChanges(added=added, updated=updated, removed_ids=removed_ids)


def describe_conversation(
    messages: list[ConversationMessage],
    categories: list[MemoryCategory],
    items_by_number: dict[int, MemoryItem],
) -> str:
    """Write what the post-conversation processing model is given.

    Args:
        messages: The Conversation's messages, oldest first.
        categories: Every Memory Category, archived ones included.
        items_by_number: The User's current Memory Items, by number.

    Returns:
        The Memory Categories new items may go in, what is already
        remembered, and the Conversation.
    """
    category_names = {category.id: category.name for category in categories}
    category_lines = "\n".join(
        f"- {category.name}: {category.description}"
        for category in categories
        if not category.archived
    )
    item_lines = "\n".join(
        f"[{number}] ({category_names.get(item.category_id, 'Other')}) {item.content}"
        for number, item in items_by_number.items()
    )
    return (
        f"Memory Categories:\n{category_lines}\n\n"
        f"What is remembered now:\n{item_lines or 'Nothing yet.'}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages)}"
    )


class PostConversationProcessor:
    """Sums up each ended Conversation and updates the User's Memory Items."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        chat_model: UsageRecordingChatModel,
        clock: Clock,
    ) -> None:
        """Set up the processor.

        Args:
            repositories: Where Users, Conversations, User Memory and
                settings are stored.
            features: Says whether User Memory works for the User.
            chat_model: Writes the summary and the Memory Item operations,
                and records the tokens used.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._features = features
        self._chat_model = chat_model
        self._clock = clock

    def process(self, conversation: Conversation) -> None:
        """Process one ended Conversation and mark it processed.

        Nothing is saved when User Memory doesn't work for the User. One
        model call gives the summary and the operations; an unreadable
        answer is asked again once, and if it is still unreadable nothing is
        saved, so a bad answer is never retried forever.

        Args:
            conversation: The ended Conversation.

        Raises:
            Exception: Whatever the chat model raises; the Conversation stays
                unprocessed so the next tick tries again.
        """
        user_memory = self._repositories.user_memory
        user = self._repositories.users.get(conversation.user_id)
        messages = self._repositories.conversations.list_messages(conversation.id)
        if (
            user is None
            or not self._features.works_for(user.id, Feature.USER_MEMORY)
            or not messages
        ):
            user_memory.save_processed_conversation(
                conversation.id, self._clock.now(), None, NO_CHANGES
            )
            return
        categories = self._repositories.memory_categories.list_all()
        items_by_number = dict(enumerate(user_memory.list_items(user.id), start=1))
        answer = self._ask(
            user.id, describe_conversation(messages, categories, items_by_number)
        )
        if answer is None:
            logger.warning("Post-conversation processing gave no readable answer")
            user_memory.save_processed_conversation(
                conversation.id, self._clock.now(), None, NO_CHANGES
            )
            return
        now = self._clock.now()
        changes = plan_memory_changes(
            answer.operations,
            MemoryChangeContext(
                user_id=user.id,
                conversation_id=conversation.id,
                now=now,
                items_by_number=items_by_number,
                active_categories={
                    category.name.lower(): category
                    for category in categories
                    if not category.archived
                },
            ),
        )
        summary = ConversationSummary(
            id=uuid4(),
            conversation_id=conversation.id,
            user_id=user.id,
            summary=answer.summary,
            mood=answer.mood,
            created_at=now,
        )
        user_memory.save_processed_conversation(conversation.id, now, summary, changes)

    def _ask(self, user_id: UUID, description: str) -> ProcessingAnswer | None:
        """Ask the model about the Conversation, once more if it can't be read.

        Args:
            user_id: The User whose Conversation it was.
            description: The categories, current memory and Conversation.

        Returns:
            The answer, or None if both answers were unreadable.
        """
        settings = self._repositories.platform_settings
        for _ in range(2):
            answer = self._chat_model.generate(
                user_id=user_id,
                model=settings.get("memory_processing_model"),
                instructions=settings.get("memory_processing_prompt"),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            processing_answer = read_processing_answer(answer)
            if processing_answer is not None:
                return processing_answer
        return None
