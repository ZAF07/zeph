from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.life_threads import name_keys
from companion.core.models import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
    Curiosity,
    CuriosityChanges,
    CuriositySensitivity,
    CuriosityState,
    LifeThread,
    LifeThreadToSave,
    MemoryChanges,
    MemoryItem,
    MemorySource,
    MessageDirection,
    MessageKind,
    ThreadReaction,
    UserPortrait,
)
from companion.core.ports import Embedder, Repositories
from evals.cases import EarlierLine, EvalCuriosity, EvalMemory, EvalThread

MEMORY_ITEMS_DAYS_AGO = 30


def open_conversation_with(
    repositories: Repositories,
    user_id: UUID,
    earlier: Sequence[EarlierLine],
    now: datetime,
) -> UUID | None:
    """Start an open Conversation holding some earlier messages.

    The messages are a minute apart and the last one a minute before `now`,
    so the next Message the User sends joins this Conversation.

    Args:
        repositories: Where Conversations are stored.
        user_id: The User's ID.
        earlier: The messages, oldest first.
        now: When the next Message will be sent.

    Returns:
        The Conversation's ID; None, with nothing saved, if there are no
        messages.
    """
    if not earlier:
        return None
    started_at = now - timedelta(minutes=len(earlier))
    conversation = Conversation(
        id=uuid4(),
        user_id=user_id,
        started_at=started_at,
        last_message_at=now - timedelta(minutes=1),
    )
    repositories.conversations.add(conversation)
    for number, line in enumerate(earlier):
        repositories.conversations.add_message(
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation.id,
                direction=(
                    MessageDirection.INCOMING
                    if line.from_person
                    else MessageDirection.OUTGOING
                ),
                kind=MessageKind.TEXT,
                content=line.text,
                sent_at=started_at + timedelta(minutes=number),
            )
        )
    return conversation.id


def give_made_up_memory(
    repositories: Repositories,
    embedder: Embedder,
    user_id: UUID,
    memory: EvalMemory,
    now: datetime,
    open_conversation_id: UUID | None,
) -> None:
    """Save a made-up User Memory for a User, as if it was learned earlier.

    Everything is saved through the repositories, with embeddings made the
    way the Companion makes them, so the reply path finds it as it would
    find real memory. Knowledge Documents aren't saved here; an Admin
    uploads them.

    Args:
        repositories: Where the User Memory is stored.
        embedder: Embeds the Summaries and Life Threads.
        user_id: The User's ID.
        memory: The made-up memory.
        now: When the case's first Message is sent.
        open_conversation_id: The open Conversation, for Threads already
            raised in it; None if there is none.

    Raises:
        ValueError: If a Memory Item names a Memory Category that doesn't
            exist.
    """
    if memory.portrait:
        repositories.user_portraits.save(
            UserPortrait(
                user_id=user_id,
                text=memory.portrait,
                written_at=now - timedelta(days=1),
            )
        )
    save_memory_items(repositories, user_id, memory.items, now)
    for summary in memory.summaries:
        written_at = now - timedelta(days=summary.days_ago)
        conversation_id = add_ended_conversation(repositories, user_id, written_at)
        [embedding] = embedder.embed_passages([summary.summary])
        repositories.user_memory.save_processed_conversation(
            conversation_id,
            written_at,
            ConversationSummary(
                id=uuid4(),
                conversation_id=conversation_id,
                user_id=user_id,
                summary=summary.summary,
                mood=summary.mood,
                created_at=written_at,
            ),
            MemoryChanges(added=[], updated=[], removed_ids=[]),
            summary_embedding=embedding,
        )
    repositories.life_threads.save_many(
        added=[
            to_thread_to_save(embedder, user_id, thread, now, open_conversation_id)
            for thread in memory.threads
        ],
        changed=[],
    )
    repositories.curiosities.save_changes(
        CuriosityChanges(
            added=[
                to_curiosity(user_id, curiosity, now)
                for curiosity in memory.curiosities
            ],
            updated=[],
            reactions={},
        )
    )


def add_ended_conversation(
    repositories: Repositories, user_id: UUID, at: datetime
) -> UUID:
    """Add an ended Conversation from the past, for memory learned in it.

    Args:
        repositories: Where Conversations are stored.
        user_id: The User's ID.
        at: When it happened.

    Returns:
        Its ID.
    """
    conversation = Conversation(
        id=uuid4(),
        user_id=user_id,
        started_at=at,
        last_message_at=at,
        ended_at=at,
    )
    repositories.conversations.add(conversation)
    return conversation.id


def save_memory_items(
    repositories: Repositories,
    user_id: UUID,
    items: dict[str, list[str]],
    now: datetime,
) -> None:
    """Save Memory Items as if they were learned in a Conversation a while ago.

    Args:
        repositories: Where Memory Items are stored.
        user_id: The User's ID.
        items: The items' contents by Memory Category name.
        now: When the case's first Message is sent.

    Raises:
        ValueError: If a Memory Category name doesn't exist.
    """
    if not items:
        return
    categories = {
        category.name: category.id
        for category in repositories.memory_categories.list_all()
    }
    unknown = [name for name in items if name not in categories]
    if unknown:
        raise ValueError(f"No such Memory Category: {', '.join(unknown)}")
    learned_at = now - timedelta(days=MEMORY_ITEMS_DAYS_AGO)
    conversation_id = add_ended_conversation(repositories, user_id, learned_at)
    added = [
        MemoryItem(
            id=uuid4(),
            user_id=user_id,
            category_id=categories[name],
            content=content,
            source=MemorySource.CONVERSATION,
            source_conversation_id=conversation_id,
            created_at=learned_at,
            updated_at=learned_at,
        )
        for name, contents in items.items()
        for content in contents
    ]
    repositories.user_memory.save_processed_conversation(
        conversation_id,
        learned_at,
        None,
        MemoryChanges(added=added, updated=[], removed_ids=[]),
    )


def to_thread_to_save(
    embedder: Embedder,
    user_id: UUID,
    thread: EvalThread,
    now: datetime,
    open_conversation_id: UUID | None,
) -> LifeThreadToSave:
    """Make a Life Thread to save, with its name keys and embedding.

    It is embedded as the Thread keeper embeds Threads: its title, then its
    story.

    Args:
        embedder: Embeds its title and story.
        user_id: The User's ID.
        thread: The made-up Thread.
        now: When the case's first Message is sent.
        open_conversation_id: The open Conversation, if it was raised there.

    Returns:
        The Thread to save.
    """
    updated_at = now - timedelta(days=thread.updated_days_ago)
    last_raised_at = None
    last_raised_conversation_id = None
    if thread.raised_in_this_conversation:
        last_raised_at = now - timedelta(minutes=2)
        last_raised_conversation_id = open_conversation_id
    elif thread.raised_days_ago is not None:
        last_raised_at = now - timedelta(days=thread.raised_days_ago)
    [embedding] = embedder.embed_passages([f"{thread.title}. {thread.story}"])
    return LifeThreadToSave(
        thread=LifeThread(
            id=uuid4(),
            user_id=user_id,
            title=thread.title,
            story=thread.story,
            people=tuple(thread.people),
            is_open=thread.is_open,
            started_at=updated_at,
            updated_at=updated_at,
            last_raised_at=last_raised_at,
            last_raised_conversation_id=last_raised_conversation_id,
            last_reaction=ThreadReaction(thread.reaction) if thread.reaction else None,
        ),
        name_keys=name_keys(thread.people),
        embedding=embedding,
    )


def to_curiosity(user_id: UUID, curiosity: EvalCuriosity, now: datetime) -> Curiosity:
    """Make a waiting Curiosity to save.

    Args:
        user_id: The User's ID.
        curiosity: The made-up Curiosity.
        now: When the case's first Message is sent.

    Returns:
        The Curiosity, written three days before `now`.
    """
    not_before = (
        None
        if curiosity.not_before_days_ago is None
        else (now - timedelta(days=curiosity.not_before_days_ago)).date()
    )
    return Curiosity(
        id=uuid4(),
        user_id=user_id,
        question=curiosity.question,
        why=curiosity.why,
        not_before=not_before,
        sensitivity=CuriositySensitivity(curiosity.sensitivity),
        state=CuriosityState.WAITING,
        created_at=now - timedelta(days=3),
    )
