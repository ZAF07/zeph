from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict
from datetime import date, datetime
from functools import partial
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import (
    Connection,
    Engine,
    Row,
    Select,
    and_,
    bindparam,
    delete,
    func,
    or_,
    select,
    tuple_,
    update,
)
from sqlalchemy.dialects.postgresql import aggregate_order_by, distinct_on, insert

from companion.adapters.postgres.tables import (
    check_in_kinds,
    check_ins,
    connection_tokens,
    conversation_messages,
    conversation_summaries,
    conversations,
    daily_usage,
    feature_switches,
    helplines,
    knowledge_documents,
    memory_categories,
    memory_items,
    model_calls,
    needs,
    pending_auth_account_deletions,
    personal_stickers,
    platform_settings,
    safeguard_events,
    shared_photos,
    stickers,
    telegram_connections,
    understandings,
    user_feature_switches,
    users,
)
from companion.core.features import feature_details
from companion.core.models import (
    ChannelPhoto,
    ChannelSticker,
    ChatLine,
    ChatRole,
    ChatSetting,
    CheckIn,
    CheckInFrequency,
    CheckInKind,
    CheckInKindDetails,
    CheckInKindOverview,
    CheckInLogEntry,
    CheckInOutcome,
    CheckInSettings,
    ConnectionToken,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    DailyUsage,
    Feature,
    FeatureSwitch,
    Helpline,
    HelplineDetails,
    KnowledgeDetailsChange,
    KnowledgeDocument,
    KnowledgeFile,
    KnowledgeFileType,
    KnowledgeStatus,
    KnowledgeUpload,
    LibrarySticker,
    MemoryCategory,
    MemoryCategoryDetails,
    MemoryCategoryOverview,
    MemoryChanges,
    MemoryItem,
    MemorySource,
    MessageDirection,
    MessageKind,
    ModelCall,
    ModelCallContent,
    ModelCallTrace,
    ModelCallTraceDetails,
    ModelCallTraceOverview,
    ModelStep,
    MoodIntensity,
    Need,
    NextDueTimeChange,
    OfferedTool,
    PersonalSticker,
    PlatformSettings,
    RiskType,
    SafeguardEvent,
    SafeguardEventOverview,
    SharedPhoto,
    StoredSetting,
    TelegramConnection,
    ToolCallRecord,
    TraceKind,
    Understanding,
    UnderstandingForm,
    User,
    UserOverview,
    UserRole,
)
from companion.core.ports import Repositories, Transaction


class Database(Protocol):
    """Where a repository runs its queries: the engine, or one open transaction."""

    def connect(self) -> AbstractContextManager[Connection]:
        """Open a connection for reading.

        Returns:
            The connection, as a context manager.
        """
        ...

    def begin(self) -> AbstractContextManager[Connection]:
        """Open a connection whose changes are saved together.

        Returns:
            The connection, as a context manager.
        """
        ...


def _to_user(row: Row[Any]) -> User:
    """Turn a `users` row into a User.

    Args:
        row: The database row.

    Returns:
        The User.
    """
    return User(
        id=row.id,
        auth_id=row.auth_id,
        email=row.email,
        created_at=row.created_at,
        name=row.name,
        onboarding_reasons=tuple(row.onboarding_reasons),
        onboarding_note=row.onboarding_note,
        country=row.country,
        time_zone=row.time_zone,
        ai_notice_acknowledged_at=row.ai_notice_acknowledged_at,
        user_memory_enabled=row.user_memory_enabled,
        photo_viewing_enabled=row.photo_viewing_enabled,
        onboarding_completed_at=row.onboarding_completed_at,
        role=UserRole(row.role),
        check_ins=CheckInSettings(
            enabled=row.check_ins_enabled,
            frequency=CheckInFrequency(row.check_in_frequency),
            quiet_hours_start=row.quiet_hours_start,
            quiet_hours_end=row.quiet_hours_end,
            paused=row.check_ins_paused,
            paused_until=row.check_ins_paused_until,
            next_due_at=row.check_in_next_due_at,
        ),
        settings_changed_in_chat={
            ChatSetting(setting): datetime.fromisoformat(changed_at)
            for setting, changed_at in row.settings_changed_in_chat.items()
        },
        data_deletion_requested_at=row.data_deletion_requested_at,
    )


def _to_check_in_kind(row: Row[Any]) -> CheckInKind:
    """Turn a `check_in_kinds` row into a CheckInKind.

    Args:
        row: The database row.

    Returns:
        The Check-in Kind.
    """
    return CheckInKind(
        id=row.id,
        name=row.name,
        description=row.description,
        sort_order=row.sort_order,
        sends_shared_photo=row.sends_shared_photo,
    )


def _to_connection(row: Row[Any]) -> TelegramConnection:
    """Turn a `telegram_connections` row into a TelegramConnection.

    Args:
        row: The database row.

    Returns:
        The Telegram Connection.
    """
    return TelegramConnection(
        user_id=row.user_id,
        telegram_user_id=row.telegram_user_id,
        telegram_chat_id=row.telegram_chat_id,
        telegram_username=row.telegram_username,
        connected_at=row.connected_at,
    )


def _to_token(row: Row[Any]) -> ConnectionToken:
    """Turn a `connection_tokens` row into a ConnectionToken.

    Args:
        row: The database row.

    Returns:
        The connection token.
    """
    return ConnectionToken(
        user_id=row.user_id,
        token=row.token,
        created_at=row.created_at,
        expires_at=row.expires_at,
        used_at=row.used_at,
        rejected_at=row.rejected_at,
    )


def _to_conversation(row: Row[Any]) -> Conversation:
    """Turn a `conversations` row into a Conversation.

    Args:
        row: The database row.

    Returns:
        The Conversation.
    """
    return Conversation(
        id=row.id,
        user_id=row.user_id,
        started_at=row.started_at,
        last_message_at=row.last_message_at,
        ended_at=row.ended_at,
    )


def _to_message(row: Row[Any]) -> ConversationMessage:
    """Turn a `conversation_messages` row into a ConversationMessage.

    Args:
        row: The database row.

    Returns:
        The message.
    """
    return ConversationMessage(
        id=row.id,
        conversation_id=row.conversation_id,
        direction=MessageDirection(row.direction),
        kind=MessageKind(row.kind),
        content=row.content,
        sent_at=row.sent_at,
        photos=tuple(ChannelPhoto(**photo) for photo in row.photos),
        sticker=ChannelSticker(**row.sticker) if row.sticker else None,
    )


def _to_memory_category(row: Row[Any]) -> MemoryCategory:
    """Turn a `memory_categories` row into a MemoryCategory.

    Args:
        row: The database row.

    Returns:
        The Memory Category.
    """
    return MemoryCategory(
        id=row.id,
        name=row.name,
        description=row.description,
        always_include=row.always_include,
        archived=row.archived,
        sort_order=row.sort_order,
    )


def _to_library_sticker(row: Row[Any]) -> LibrarySticker:
    """Turn a `stickers` row into a LibrarySticker.

    Args:
        row: The database row.

    Returns:
        The sticker.
    """
    return LibrarySticker(
        id=row.id,
        file_id=row.file_id,
        file_unique_id=row.file_unique_id,
        emoji=row.emoji,
        set_name=row.set_name,
        preview_file_id=row.preview_file_id,
        note=row.note,
        added_at=row.added_at,
    )


def _to_personal_sticker(row: Row[Any]) -> PersonalSticker:
    """Turn a `personal_stickers` row into a PersonalSticker.

    Args:
        row: The database row.

    Returns:
        The sticker.
    """
    return PersonalSticker(
        id=row.id,
        user_id=row.user_id,
        file_id=row.file_id,
        file_unique_id=row.file_unique_id,
        emoji=row.emoji,
        set_name=row.set_name,
        preview_file_id=row.preview_file_id,
        note=row.note,
        kept_at=row.kept_at,
        last_used_at=row.last_used_at,
    )


def _to_memory_item(row: Row[Any]) -> MemoryItem:
    """Turn a `memory_items` row into a MemoryItem.

    Args:
        row: The database row.

    Returns:
        The Memory Item.
    """
    return MemoryItem(
        id=row.id,
        user_id=row.user_id,
        category_id=row.category_id,
        content=row.content,
        source=MemorySource(row.source),
        source_conversation_id=row.source_conversation_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _memory_item_values(item: MemoryItem) -> dict[str, Any]:
    """Turn a MemoryItem into the values of a `memory_items` row.

    Args:
        item: The Memory Item.

    Returns:
        The column values.
    """
    return {
        "id": item.id,
        "user_id": item.user_id,
        "category_id": item.category_id,
        "content": item.content,
        "source": item.source.value,
        "source_conversation_id": item.source_conversation_id,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


SUMMARY_COLUMNS = [
    column for column in conversation_summaries.c if column.name != "embedding"
]


def _to_summary(row: Row[Any]) -> ConversationSummary:
    """Turn a `conversation_summaries` row into a ConversationSummary.

    Args:
        row: The database row.

    Returns:
        The Conversation Summary.
    """
    return ConversationSummary(
        id=row.id,
        conversation_id=row.conversation_id,
        user_id=row.user_id,
        summary=row.summary,
        mood=row.mood,
        created_at=row.created_at,
    )


def _to_shared_photo(row: Row[Any]) -> SharedPhoto:
    """Turn a `shared_photos` row into a SharedPhoto.

    Args:
        row: The database row.

    Returns:
        The Shared Photo.
    """
    return SharedPhoto(
        id=row.id,
        user_id=row.user_id,
        file_id=row.file_id,
        file_unique_id=row.file_unique_id,
        description=row.description,
        note=row.note,
        caption=row.caption,
        sent_at=row.sent_at,
        conversation_id=row.conversation_id,
    )


def _to_knowledge_document(row: Row[Any]) -> KnowledgeDocument:
    """Turn a `knowledge_documents` row into a Knowledge document.

    Args:
        row: The database row.

    Returns:
        The document, without its file.
    """
    return KnowledgeDocument(
        id=row.id,
        title=row.title,
        source=row.source,
        tradition=row.tradition,
        file_name=row.file_name,
        file_type=KnowledgeFileType(row.file_type),
        status=KnowledgeStatus(row.status),
        failure_reason=row.failure_reason,
        text_edited=row.text_edited,
        created_at=row.created_at,
    )


def _to_helpline(row: Row[Any]) -> Helpline:
    """Turn a `helplines` row into a Helpline.

    Args:
        row: The database row.

    Returns:
        The Helpline.
    """
    return Helpline(
        id=row.id,
        country=row.country,
        details=HelplineDetails(name=row.name, number=row.number, hours=row.hours),
        sort_order=row.sort_order,
    )


class PostgresUserRepository:
    """Stores Users in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def get(self, user_id: UUID) -> User | None:
        """Find a User by our ID.

        Args:
            user_id: The User's ID.

        Returns:
            The User, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(select(users).where(users.c.id == user_id)).first()
        return _to_user(row) if row else None

    def get_many(self, user_ids: Sequence[UUID]) -> list[User]:
        """Find many Users by our IDs, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            The Users found, in the order of the IDs given.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(users).where(users.c.id.in_(user_ids))
            ).all()
        found = {row.id: _to_user(row) for row in rows}
        return [found[user_id] for user_id in user_ids if user_id in found]

    def get_by_auth_id(self, auth_id: str) -> User | None:
        """Find a User by the auth provider's account ID.

        Args:
            auth_id: The auth provider's account ID.

        Returns:
            The User, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(users).where(users.c.auth_id == auth_id)
            ).first()
        return _to_user(row) if row else None

    def add(self, user: User) -> User:
        """Save a new User, or return the existing one with the same auth ID.

        Args:
            user: The User to save.

        Returns:
            The saved User.
        """
        statement = (
            insert(users)
            .values(
                id=user.id,
                auth_id=user.auth_id,
                email=user.email,
                created_at=user.created_at,
                role=user.role.value,
            )
            .on_conflict_do_nothing(index_elements=[users.c.auth_id])
        )
        with self._database.begin() as connection:
            connection.execute(statement)
            row = connection.execute(
                select(users).where(users.c.auth_id == user.auth_id)
            ).one()
        return _to_user(row)

    def update(self, user: User) -> User:
        """Save changes to an existing User's profile and preferences.

        Args:
            user: The User with their new values.

        Returns:
            The saved User.
        """
        statement = (
            update(users)
            .where(users.c.id == user.id)
            .values(
                name=user.name,
                onboarding_reasons=list(user.onboarding_reasons),
                onboarding_note=user.onboarding_note,
                country=user.country,
                time_zone=user.time_zone,
                ai_notice_acknowledged_at=user.ai_notice_acknowledged_at,
                user_memory_enabled=user.user_memory_enabled,
                photo_viewing_enabled=user.photo_viewing_enabled,
                onboarding_completed_at=user.onboarding_completed_at,
                check_ins_enabled=user.check_ins.enabled,
                check_in_frequency=user.check_ins.frequency.value,
                quiet_hours_start=user.check_ins.quiet_hours_start,
                quiet_hours_end=user.check_ins.quiet_hours_end,
                check_ins_paused=user.check_ins.paused,
                check_ins_paused_until=user.check_ins.paused_until,
                check_in_next_due_at=user.check_ins.next_due_at,
                settings_changed_in_chat={
                    setting.value: changed_at.isoformat()
                    for setting, changed_at in user.settings_changed_in_chat.items()
                },
                data_deletion_requested_at=user.data_deletion_requested_at,
            )
            .returning(users)
        )
        with self._database.begin() as connection:
            row = connection.execute(statement).one()
        return _to_user(row)

    def list_overviews(self) -> list[UserOverview]:
        """List every User with their activity counts, newest sign-up first.

        Returns:
            One overview per User.
        """
        conversation_count = (
            select(func.count())
            .select_from(conversations)
            .where(conversations.c.user_id == users.c.id)
            .scalar_subquery()
        )
        messages_sent = (
            select(func.count())
            .select_from(conversation_messages.join(conversations))
            .where(
                conversations.c.user_id == users.c.id,
                conversation_messages.c.direction == MessageDirection.INCOMING.value,
            )
            .scalar_subquery()
        )
        telegram_connected = (
            select(telegram_connections.c.user_id)
            .where(telegram_connections.c.user_id == users.c.id)
            .exists()
        )
        statement = select(
            users,
            telegram_connected.label("telegram_connected"),
            conversation_count.label("conversation_count"),
            messages_sent.label("messages_sent"),
        ).order_by(users.c.created_at.desc())
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [
            UserOverview(
                user=_to_user(row),
                telegram_connected=row.telegram_connected,
                conversation_count=row.conversation_count,
                messages_sent=row.messages_sent,
            )
            for row in rows
        ]

    def count_admins(self) -> int:
        """Count the Users who are Admins.

        Returns:
            How many Admins there are.
        """
        with self._database.connect() as connection:
            admin_count = connection.execute(
                select(func.count())
                .select_from(users)
                .where(users.c.role == UserRole.ADMIN.value)
            ).scalar_one()
        return int(admin_count)

    def promote_to_admin(self, user_id: UUID) -> User:
        """Make a User an Admin.

        Args:
            user_id: The User's ID.

        Returns:
            The saved User.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(role=UserRole.ADMIN.value)
                .returning(users)
            ).one()
        return _to_user(row)

    def demote_to_user(self, user_id: UUID) -> User:
        """Make an Admin a plain User.

        Args:
            user_id: The Admin's ID.

        Returns:
            The saved User.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(users)
                .where(users.c.id == user_id)
                .values(role=UserRole.USER.value)
                .returning(users)
            ).one()
        return _to_user(row)

    def delete(self, user_id: UUID) -> bool:
        """Delete a User: their profile and settings.

        Any rows of theirs still left go through the tables' cascading
        foreign keys.

        Args:
            user_id: The User's ID.

        Returns:
            True if they were deleted; False if there was no such User.
        """
        with self._database.begin() as connection:
            deleted_id = connection.execute(
                delete(users).where(users.c.id == user_id).returning(users.c.id)
            ).scalar_one_or_none()
        return deleted_id is not None


class PostgresPendingAuthAccountDeletionRepository:
    """Stores the auth provider accounts still to delete in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_auth_ids(self) -> list[str]:
        """List the auth IDs of the accounts still to delete, oldest first.

        Returns:
            The auth IDs.
        """
        with self._database.connect() as connection:
            return list(
                connection.execute(
                    select(pending_auth_account_deletions.c.auth_id).order_by(
                        pending_auth_account_deletions.c.added_at
                    )
                ).scalars()
            )

    def add(self, auth_id: str, added_at: datetime) -> None:
        """Note an auth provider account as still to delete.

        Adding one already on the list changes nothing.

        Args:
            auth_id: The auth provider's account ID.
            added_at: When it was added.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(pending_auth_account_deletions)
                .values(auth_id=auth_id, added_at=added_at)
                .on_conflict_do_nothing()
            )

    def complete(self, auth_id: str) -> None:
        """Take an account off the list, once it is deleted at the auth provider.

        Args:
            auth_id: The auth provider's account ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(pending_auth_account_deletions).where(
                    pending_auth_account_deletions.c.auth_id == auth_id
                )
            )


class PostgresTelegramConnectionRepository:
    """Stores Telegram Connections in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def get_by_user(self, user_id: UUID) -> TelegramConnection | None:
        """Find a User's Telegram Connection.

        Args:
            user_id: The User's ID.

        Returns:
            The connection, or None if the User has none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(telegram_connections).where(
                    telegram_connections.c.user_id == user_id
                )
            ).first()
        return _to_connection(row) if row else None

    def list_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, TelegramConnection]:
        """Find many Users' Telegram Connections, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            Each User's connection; a User with none is left out.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(telegram_connections).where(
                    telegram_connections.c.user_id.in_(user_ids)
                )
            ).all()
        return {row.user_id: _to_connection(row) for row in rows}

    def get_by_telegram_user(self, telegram_user_id: int) -> TelegramConnection | None:
        """Find the Telegram Connection for a Telegram account.

        Args:
            telegram_user_id: The Telegram account's ID.

        Returns:
            The connection, or None if the account is not connected.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(telegram_connections).where(
                    telegram_connections.c.telegram_user_id == telegram_user_id
                )
            ).first()
        return _to_connection(row) if row else None

    def save(self, connection: TelegramConnection) -> None:
        """Save a User's Telegram Connection, replacing any they had.

        Args:
            connection: The connection to save.
        """
        values = {
            "user_id": connection.user_id,
            "telegram_user_id": connection.telegram_user_id,
            "telegram_chat_id": connection.telegram_chat_id,
            "telegram_username": connection.telegram_username,
            "connected_at": connection.connected_at,
        }
        statement = (
            insert(telegram_connections)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[telegram_connections.c.user_id], set_=values
            )
        )
        with self._database.begin() as db:
            db.execute(statement)

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Telegram Connection.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(telegram_connections).where(
                    telegram_connections.c.user_id == user_id
                )
            )


class PostgresConnectionTokenRepository:
    """Stores connection tokens in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def add(self, token: ConnectionToken) -> None:
        """Save a new connection token.

        Args:
            token: The token to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(connection_tokens).values(
                    token=token.token,
                    user_id=token.user_id,
                    created_at=token.created_at,
                    expires_at=token.expires_at,
                    used_at=token.used_at,
                    rejected_at=token.rejected_at,
                )
            )

    def get(self, token: str) -> ConnectionToken | None:
        """Find a connection token by its code.

        Args:
            token: The code.

        Returns:
            The token, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(connection_tokens).where(connection_tokens.c.token == token)
            ).first()
        return _to_token(row) if row else None

    def get_latest_for_user(self, user_id: UUID) -> ConnectionToken | None:
        """Find the newest connection token a User asked for.

        Args:
            user_id: The User's ID.

        Returns:
            The newest token, or None if the User has never asked for one.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(connection_tokens)
                .where(connection_tokens.c.user_id == user_id)
                .order_by(connection_tokens.c.created_at.desc())
                .limit(1)
            ).first()
        return _to_token(row) if row else None

    def claim(self, token: str, used_at: datetime) -> bool:
        """Mark a token used, in one step, only if it is still active.

        Args:
            token: The code.
            used_at: When it is being used.

        Returns:
            True if this call claimed the token; False if it was already used,
            refused or expired, so two requests can never both use one token.
        """
        with self._database.begin() as connection:
            claimed = connection.execute(
                update(connection_tokens)
                .where(
                    connection_tokens.c.token == token,
                    connection_tokens.c.used_at.is_(None),
                    connection_tokens.c.rejected_at.is_(None),
                    connection_tokens.c.expires_at > used_at,
                )
                .values(used_at=used_at)
                .returning(connection_tokens.c.token)
            ).first()
        return claimed is not None

    def mark_rejected(self, token: str, rejected_at: datetime) -> None:
        """Record that a token was refused because the Telegram account is taken.

        Args:
            token: The code.
            rejected_at: When it was refused.
        """
        with self._database.begin() as connection:
            connection.execute(
                update(connection_tokens)
                .where(connection_tokens.c.token == token)
                .values(rejected_at=rejected_at)
            )

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete every connection token of a User's.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(connection_tokens).where(connection_tokens.c.user_id == user_id)
            )


class PostgresConversationRepository:
    """Stores Conversations and their messages in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def get_latest_for_user(self, user_id: UUID) -> Conversation | None:
        """Find a User's newest Conversation.

        Args:
            user_id: The User's ID.

        Returns:
            The newest Conversation, or None if the User has never had one.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(conversations)
                .where(conversations.c.user_id == user_id)
                .order_by(conversations.c.last_message_at.desc())
                .limit(1)
            ).first()
        return _to_conversation(row) if row else None

    def list_latest_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, Conversation]:
        """Find many Users' newest Conversations, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            Each User's newest Conversation; a User who never had one is
            left out.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(conversations)
                .where(conversations.c.user_id.in_(user_ids))
                .order_by(
                    conversations.c.user_id, conversations.c.last_message_at.desc()
                )
                .ext(distinct_on(conversations.c.user_id))
            ).all()
        return {row.user_id: _to_conversation(row) for row in rows}

    def add(self, conversation: Conversation) -> None:
        """Save a new Conversation.

        Args:
            conversation: The Conversation to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(conversations).values(
                    id=conversation.id,
                    user_id=conversation.user_id,
                    started_at=conversation.started_at,
                    last_message_at=conversation.last_message_at,
                )
            )

    def add_message(self, message: ConversationMessage) -> None:
        """Save a message and make it the Conversation's newest message.

        Args:
            message: The message to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(conversation_messages).values(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    direction=message.direction.value,
                    kind=message.kind.value,
                    content=message.content,
                    sent_at=message.sent_at,
                    photos=[asdict(photo) for photo in message.photos],
                    sticker=asdict(message.sticker) if message.sticker else None,
                )
            )
            connection.execute(
                update(conversations)
                .where(conversations.c.id == message.conversation_id)
                .values(last_message_at=message.sent_at)
            )

    def add_message_if_open(self, message: ConversationMessage) -> bool:
        """Save a message, but only if its Conversation has not been ended.

        The Conversation row is updated first, which locks it, so `end_quiet`
        running at the same time either waits and then sees the new message,
        or ends the Conversation first and the message is refused.

        Args:
            message: The message to save.

        Returns:
            True if it was saved; False if the Conversation was ended.
        """
        with self._database.begin() as connection:
            open_conversation = connection.execute(
                update(conversations)
                .where(
                    conversations.c.id == message.conversation_id,
                    conversations.c.ended_at.is_(None),
                )
                .values(last_message_at=message.sent_at)
                .returning(conversations.c.id)
            ).first()
            if open_conversation is None:
                return False
            connection.execute(
                insert(conversation_messages).values(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    direction=message.direction.value,
                    kind=message.kind.value,
                    content=message.content,
                    sent_at=message.sent_at,
                    photos=[asdict(photo) for photo in message.photos],
                    sticker=asdict(message.sticker) if message.sticker else None,
                )
            )
        return True

    def list_messages(self, conversation_id: UUID) -> list[ConversationMessage]:
        """List a Conversation's messages in the order they were saved.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The messages.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(conversation_messages)
                .where(conversation_messages.c.conversation_id == conversation_id)
                .order_by(conversation_messages.c.position)
            ).all()
        return [_to_message(row) for row in rows]

    def end_quiet(self, quiet_since: datetime, ended_at: datetime) -> None:
        """End every open Conversation with no message since a given time.

        Args:
            quiet_since: Conversations whose newest message is at or before
                this time are ended.
            ended_at: When they are being ended.
        """
        with self._database.begin() as connection:
            connection.execute(
                update(conversations)
                .where(
                    conversations.c.ended_at.is_(None),
                    conversations.c.last_message_at <= quiet_since,
                )
                .values(ended_at=ended_at)
            )

    def list_ended_unprocessed(self) -> list[Conversation]:
        """List ended Conversations not yet processed, oldest first.

        Returns:
            The Conversations.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(conversations)
                .where(
                    conversations.c.ended_at.is_not(None),
                    conversations.c.processed_at.is_(None),
                )
                .order_by(conversations.c.ended_at)
            ).all()
        return [_to_conversation(row) for row in rows]

    def delete_messages_sent_before(self, cutoff: datetime) -> None:
        """Delete every message sent before a time; Conversations stay.

        Args:
            cutoff: Messages sent before this are deleted.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(conversation_messages).where(
                    conversation_messages.c.sent_at < cutoff
                )
            )

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Conversations and their messages.

        The messages go through the table's cascading foreign key.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(conversations).where(conversations.c.user_id == user_id)
            )


class PostgresPlatformSettingsRepository:
    """Reads platform settings from Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def load(self) -> PlatformSettings:
        """Read every setting in one query.

        Returns:
            The settings as they are now.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(platform_settings.c.key, platform_settings.c.value)
            ).all()
        return PlatformSettings({row.key: row.value for row in rows})

    def get_many(self, keys: Sequence[str]) -> list[StoredSetting]:
        """Read several settings with when and by whom they were last saved.

        Args:
            keys: The settings' keys.

        Returns:
            The settings that exist, in the order of `keys`.
        """
        statement = (
            select(
                platform_settings.c.key,
                platform_settings.c.value,
                platform_settings.c.updated_at,
                func.coalesce(users.c.name, users.c.email).label("updated_by_name"),
            )
            .select_from(platform_settings.outerjoin(users))
            .where(platform_settings.c.key.in_(keys))
        )
        with self._database.connect() as connection:
            rows = {row.key: row for row in connection.execute(statement).all()}
        return [
            StoredSetting(
                key=key,
                value=rows[key].value,
                updated_at=rows[key].updated_at,
                updated_by_name=rows[key].updated_by_name,
            )
            for key in keys
            if key in rows
        ]

    def save_many(
        self, values: Mapping[str, Any], updated_at: datetime, updated_by: UUID
    ) -> None:
        """Save new values for several settings in one step.

        Args:
            values: The new value for each setting key.
            updated_at: When they are being saved.
            updated_by: The Admin saving them.
        """
        with self._database.begin() as connection:
            for key, value in values.items():
                connection.execute(
                    update(platform_settings)
                    .where(platform_settings.c.key == key)
                    .values(value=value, updated_at=updated_at, updated_by=updated_by)
                )


class PostgresHelplineRepository:
    """Stores Helplines in Postgres; the international fallback has no country."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_countries(self) -> list[Helpline]:
        """List every country's Helplines, by country and then sort order.

        Returns:
            The Helplines, without the international fallback.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(helplines)
                .where(helplines.c.country.is_not(None))
                .order_by(helplines.c.country, helplines.c.sort_order)
            ).all()
        return [_to_helpline(row) for row in rows]

    def list_for_country(self, country: str) -> list[Helpline]:
        """List one country's Helplines in sort order.

        Args:
            country: Two-letter country code.

        Returns:
            The Helplines; empty if the country has none.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(helplines)
                .where(helplines.c.country == country)
                .order_by(helplines.c.sort_order)
            ).all()
        return [_to_helpline(row) for row in rows]

    def get(self, helpline_id: UUID) -> Helpline | None:
        """Find a Helpline, the international fallback included.

        Args:
            helpline_id: The Helpline's ID.

        Returns:
            The Helpline, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(helplines).where(helplines.c.id == helpline_id)
            ).first()
        return _to_helpline(row) if row else None

    def get_international_fallback(self) -> Helpline:
        """Read the international fallback.

        Returns:
            The international fallback.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(helplines).where(helplines.c.country.is_(None))
            ).one()
        return _to_helpline(row)

    def add(self, country: str, details: HelplineDetails) -> Helpline:
        """Save a new Helpline last in its country's list.

        Args:
            country: Two-letter country code.
            details: Its name, number and hours.

        Returns:
            The saved Helpline.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                insert(helplines)
                .values(
                    id=uuid4(),
                    country=country,
                    name=details.name,
                    number=details.number,
                    hours=details.hours,
                    sort_order=self._next_sort_order(connection, country),
                )
                .returning(helplines)
            ).one()
        return _to_helpline(row)

    def update(
        self, helpline_id: UUID, country: str | None, details: HelplineDetails
    ) -> Helpline:
        """Change a Helpline; one moved to another country goes last there.

        Args:
            helpline_id: The Helpline's ID.
            country: Its country; None only for the international fallback.
            details: Its new name, number and hours.

        Returns:
            The saved Helpline.
        """
        with self._database.begin() as connection:
            current_country = connection.execute(
                select(helplines.c.country).where(helplines.c.id == helpline_id)
            ).scalar_one()
            values: dict[str, Any] = {
                "country": country,
                "name": details.name,
                "number": details.number,
                "hours": details.hours,
            }
            if country is not None and country != current_country:
                values["sort_order"] = self._next_sort_order(connection, country)
            row = connection.execute(
                update(helplines)
                .where(helplines.c.id == helpline_id)
                .values(**values)
                .returning(helplines)
            ).one()
        return _to_helpline(row)

    def delete(self, helpline_id: UUID) -> None:
        """Remove a Helpline.

        Args:
            helpline_id: The Helpline's ID.
        """
        with self._database.begin() as connection:
            connection.execute(delete(helplines).where(helplines.c.id == helpline_id))

    def set_sort_orders(self, sort_orders: Mapping[UUID, int]) -> None:
        """Save new sort orders for several Helplines in one step.

        Args:
            sort_orders: The new sort order for each Helpline ID.
        """
        with self._database.begin() as connection:
            for helpline_id, sort_order in sort_orders.items():
                connection.execute(
                    update(helplines)
                    .where(helplines.c.id == helpline_id)
                    .values(sort_order=sort_order)
                )

    @staticmethod
    def _next_sort_order(connection: Connection, country: str) -> int:
        """Work out the sort order that puts a Helpline last in its country.

        Args:
            connection: The open database connection.
            country: Two-letter country code.

        Returns:
            One more than the country's highest sort order, or 0.
        """
        highest = connection.execute(
            select(func.max(helplines.c.sort_order)).where(
                helplines.c.country == country
            )
        ).scalar()
        return 0 if highest is None else int(highest) + 1


class PostgresSafeguardEventRepository:
    """Stores Safeguard Events in Postgres. There is no column for message text."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def add(self, event: SafeguardEvent) -> None:
        """Save a Safeguard Event.

        Args:
            event: The event to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(safeguard_events).values(
                    id=event.id,
                    user_id=event.user_id,
                    risk_type=event.risk_type.value,
                    created_at=event.created_at,
                    helplines_country=event.helplines_country,
                )
            )

    def list_overviews(
        self, since: datetime | None, risk_type: RiskType | None
    ) -> list[SafeguardEventOverview]:
        """List Safeguard Events with who the User is, newest first.

        Args:
            since: Only events at or after this time; None for all time.
            risk_type: Only events of this risk type; None for every type.

        Returns:
            The events.
        """
        statement = (
            select(
                safeguard_events,
                users.c.name.label("user_name"),
                users.c.email.label("user_email"),
            )
            .select_from(safeguard_events.join(users))
            .order_by(safeguard_events.c.created_at.desc())
        )
        if since is not None:
            statement = statement.where(safeguard_events.c.created_at >= since)
        if risk_type is not None:
            statement = statement.where(safeguard_events.c.risk_type == risk_type.value)
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [
            SafeguardEventOverview(
                event=SafeguardEvent(
                    id=row.id,
                    user_id=row.user_id,
                    risk_type=RiskType(row.risk_type),
                    created_at=row.created_at,
                    helplines_country=row.helplines_country,
                ),
                user_name=row.user_name,
                user_email=row.user_email,
            )
            for row in rows
        ]

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Safeguard Events.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(safeguard_events).where(safeguard_events.c.user_id == user_id)
            )


class PostgresNeedRepository:
    """Stores Needs in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_all(self) -> list[Need]:
        """List every Need in sort order.

        Returns:
            The Needs.
        """
        with self._database.connect() as connection:
            rows = connection.execute(select(needs).order_by(needs.c.sort_order)).all()
        return [
            Need(
                id=row.id,
                name=row.name,
                when_it_fits=row.when_it_fits,
                how_to_reply=row.how_to_reply,
                sort_order=row.sort_order,
                is_fallback=row.is_fallback,
            )
            for row in rows
        ]


class PostgresUnderstandingRepository:
    """Stores Understandings in Postgres, each with its Message."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def add(self, understanding: Understanding) -> None:
        """Save an Understanding.

        Args:
            understanding: The Understanding to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(understandings).values(
                    id=understanding.id,
                    user_id=understanding.user_id,
                    conversation_id=understanding.conversation_id,
                    message_id=understanding.message_id,
                    form=asdict(understanding.form),
                    need=understanding.need,
                    asked_why=understanding.asked_why,
                    made_at=understanding.made_at,
                )
            )

    def list_for_conversation(self, conversation_id: UUID) -> list[Understanding]:
        """List a Conversation's Understandings, oldest first.

        Args:
            conversation_id: The Conversation's ID.

        Returns:
            The Understandings.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(understandings)
                .where(understandings.c.conversation_id == conversation_id)
                .order_by(understandings.c.position)
            ).all()
        return [
            Understanding(
                id=row.id,
                user_id=row.user_id,
                conversation_id=row.conversation_id,
                message_id=row.message_id,
                form=_to_understanding_form(row.form),
                need=row.need,
                asked_why=row.asked_why,
                made_at=row.made_at,
            )
            for row in rows
        ]


def _to_understanding_form(stored: dict[str, Any]) -> UnderstandingForm:
    """Turn a saved form back into an Understanding form.

    Args:
        stored: The form as saved.

    Returns:
        The form.
    """
    return UnderstandingForm(
        need=stored["need"],
        nuance=stored["nuance"],
        mood=stored["mood"],
        intensity=MoodIntensity(stored["intensity"]),
        cause_known=stored["cause_known"],
        memory_categories=tuple(stored["memory_categories"]),
        bring_up=tuple(stored["bring_up"]),
        left_alone=tuple(stored["left_alone"]),
        look_up_past=tuple(stored["look_up_past"]),
        knowledge=tuple(stored["knowledge"]),
        threads_touched=tuple(stored["threads_touched"]),
    )


class PostgresMemoryCategoryRepository:
    """Stores Memory Categories in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_all(self) -> list[MemoryCategory]:
        """List every Memory Category, archived ones included, in sort order.

        Returns:
            The categories.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(memory_categories).order_by(memory_categories.c.sort_order)
            ).all()
        return [_to_memory_category(row) for row in rows]

    def list_overviews(self) -> list[MemoryCategoryOverview]:
        """List every Memory Category with its Memory Item count, in sort order.

        Returns:
            The categories, archived ones included.
        """
        item_count = func.count(memory_items.c.id).label("item_count")
        with self._database.connect() as connection:
            rows = connection.execute(
                select(memory_categories, item_count)
                .outerjoin(
                    memory_items, memory_items.c.category_id == memory_categories.c.id
                )
                .group_by(memory_categories.c.id)
                .order_by(memory_categories.c.sort_order)
            ).all()
        return [
            MemoryCategoryOverview(
                category=_to_memory_category(row), item_count=row.item_count
            )
            for row in rows
        ]

    def get(self, category_id: UUID) -> MemoryCategory | None:
        """Find a Memory Category.

        Args:
            category_id: The category's ID.

        Returns:
            The category, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(memory_categories).where(memory_categories.c.id == category_id)
            ).first()
        return _to_memory_category(row) if row else None

    def add(self, details: MemoryCategoryDetails) -> MemoryCategory:
        """Save a new, active Memory Category last in the list.

        Args:
            details: Its name, description and "always include".

        Returns:
            The saved category.
        """
        with self._database.begin() as connection:
            highest = connection.execute(
                select(func.max(memory_categories.c.sort_order))
            ).scalar()
            row = connection.execute(
                insert(memory_categories)
                .values(
                    id=uuid4(),
                    name=details.name,
                    description=details.description,
                    always_include=details.always_include,
                    archived=False,
                    sort_order=0 if highest is None else int(highest) + 1,
                )
                .returning(memory_categories)
            ).one()
        return _to_memory_category(row)

    def update(self, category: MemoryCategory) -> MemoryCategory:
        """Save a Memory Category's name, description and flags.

        Args:
            category: The category with its new values.

        Returns:
            The saved category.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(memory_categories)
                .where(memory_categories.c.id == category.id)
                .values(
                    name=category.name,
                    description=category.description,
                    always_include=category.always_include,
                    archived=category.archived,
                )
                .returning(memory_categories)
            ).one()
        return _to_memory_category(row)


class PostgresUserMemoryRepository:
    """Stores Memory Items, Conversation Summaries and Shared Photos in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_items(self, user_id: UUID) -> list[MemoryItem]:
        """List a User's Memory Items in the order they were saved.

        Args:
            user_id: The User's ID.

        Returns:
            The Memory Items.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(memory_items)
                .where(memory_items.c.user_id == user_id)
                .order_by(memory_items.c.position)
            ).all()
        return [_to_memory_item(row) for row in rows]

    def delete_item(self, user_id: UUID, item_id: UUID) -> bool:
        """Delete one of a User's Memory Items.

        Args:
            user_id: The User's ID.
            item_id: The Memory Item's ID.

        Returns:
            True if it was deleted; False if the User has no such item.
        """
        with self._database.begin() as connection:
            deleted = connection.execute(
                delete(memory_items)
                .where(memory_items.c.user_id == user_id, memory_items.c.id == item_id)
                .returning(memory_items.c.id)
            ).first()
        return deleted is not None

    def delete_all_items(self, user_id: UUID) -> None:
        """Delete every one of a User's Memory Items.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(memory_items).where(memory_items.c.user_id == user_id)
            )

    def replace_onboarding_items(self, user_id: UUID, items: list[MemoryItem]) -> None:
        """Swap the User's Memory Items from onboarding for new ones, in one step.

        Args:
            user_id: The User's ID.
            items: The new Memory Items from onboarding.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(memory_items).where(
                    memory_items.c.user_id == user_id,
                    memory_items.c.source == MemorySource.ONBOARDING.value,
                )
            )
            if items:
                connection.execute(
                    insert(memory_items).values(
                        [_memory_item_values(item) for item in items]
                    )
                )

    def list_summaries(
        self, user_id: UUID, limit: int | None = None
    ) -> list[ConversationSummary]:
        """List a User's Conversation Summaries, newest first.

        Args:
            user_id: The User's ID.
            limit: The most to return; None for all of them.

        Returns:
            The Conversation Summaries.
        """
        statement = (
            select(*SUMMARY_COLUMNS)
            .where(conversation_summaries.c.user_id == user_id)
            .order_by(conversation_summaries.c.created_at.desc())
            .limit(limit)
        )
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [_to_summary(row) for row in rows]

    def find_summaries_by_meaning(
        self,
        user_id: UUID,
        embeddings: Sequence[list[float]],
        min_closeness: float,
        limit: int,
        leave_out: Sequence[UUID],
    ) -> list[ConversationSummary]:
        """Find a User's Conversation Summaries closest in meaning to any search.

        Closeness is cosine similarity. Summaries with no embedding are never
        found.

        Args:
            user_id: The User's ID; only their Summaries are searched.
            embeddings: The searches, one embedding each.
            min_closeness: How close a Summary must be to one search, from 0
                to 1.
            limit: The most to return.
            leave_out: Summaries not to return, e.g. ones already given.

        Returns:
            The closest Summaries, closest first.
        """
        if not embeddings or limit < 1:
            return []
        distance = func.least(
            *(
                conversation_summaries.c.embedding.cosine_distance(embedding)
                for embedding in embeddings
            )
        )
        statement = (
            select(*SUMMARY_COLUMNS)
            .where(
                conversation_summaries.c.user_id == user_id,
                conversation_summaries.c.embedding.is_not(None),
                conversation_summaries.c.id.not_in(leave_out),
                distance <= 1 - min_closeness,
            )
            .order_by(distance)
            .limit(limit)
        )
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [_to_summary(row) for row in rows]

    def delete_summary(self, user_id: UUID, summary_id: UUID) -> bool:
        """Delete one of a User's Conversation Summaries.

        Args:
            user_id: The User's ID.
            summary_id: The Conversation Summary's ID.

        Returns:
            True if it was deleted; False if the User has no such summary.
        """
        with self._database.begin() as connection:
            deleted = connection.execute(
                delete(conversation_summaries)
                .where(
                    conversation_summaries.c.user_id == user_id,
                    conversation_summaries.c.id == summary_id,
                )
                .returning(conversation_summaries.c.id)
            ).first()
        return deleted is not None

    def save_processed_conversation(
        self,
        conversation_id: UUID,
        processed_at: datetime,
        summary: ConversationSummary | None,
        changes: MemoryChanges,
        summary_embedding: list[float] | None = None,
    ) -> None:
        """Save what processing an ended Conversation produced, in one step.

        The Conversation is marked processed at the same time, so it is
        never processed twice.

        Args:
            conversation_id: The Conversation that was processed.
            processed_at: When processing finished.
            summary: Its Conversation Summary; None when nothing is saved.
            changes: The changes to the User's Memory Items and the new
                Shared Photos.
            summary_embedding: The Summary's embedding, so it can be found
                by meaning; None if it has none.
        """
        with self._database.begin() as connection:
            if summary is not None:
                connection.execute(
                    insert(conversation_summaries).values(
                        id=summary.id,
                        conversation_id=summary.conversation_id,
                        user_id=summary.user_id,
                        summary=summary.summary,
                        mood=summary.mood,
                        created_at=summary.created_at,
                        embedding=summary_embedding,
                    )
                )
            if changes.added:
                connection.execute(
                    insert(memory_items).values(
                        [_memory_item_values(item) for item in changes.added]
                    )
                )
            for item in changes.updated:
                connection.execute(
                    update(memory_items)
                    .where(memory_items.c.id == item.id)
                    .values(
                        category_id=item.category_id,
                        content=item.content,
                        source=item.source.value,
                        source_conversation_id=item.source_conversation_id,
                        updated_at=item.updated_at,
                    )
                )
            if changes.removed_ids:
                connection.execute(
                    delete(memory_items).where(
                        memory_items.c.id.in_(changes.removed_ids)
                    )
                )
            if changes.new_shared_photos:
                connection.execute(
                    insert(shared_photos).values(
                        [asdict(photo) for photo in changes.new_shared_photos]
                    )
                )
            connection.execute(
                update(conversations)
                .where(conversations.c.id == conversation_id)
                .values(processed_at=processed_at)
            )

    def list_shared_photos(self, user_id: UUID) -> list[SharedPhoto]:
        """List a User's Shared Photos, newest first.

        Args:
            user_id: The User's ID.

        Returns:
            The Shared Photos.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(shared_photos)
                .where(shared_photos.c.user_id == user_id)
                .order_by(shared_photos.c.sent_at.desc(), shared_photos.c.id)
            ).all()
        return [_to_shared_photo(row) for row in rows]

    def list_users_with_shared_photos(self, user_ids: Sequence[UUID]) -> set[UUID]:
        """Find which of many Users have any Shared Photos, in one query.

        Args:
            user_ids: The Users' IDs.

        Returns:
            The IDs of those with at least one Shared Photo.
        """
        with self._database.connect() as connection:
            found = connection.execute(
                select(shared_photos.c.user_id)
                .where(shared_photos.c.user_id.in_(user_ids))
                .distinct()
            ).scalars()
            return set(found)

    def get_shared_photo(self, user_id: UUID, photo_id: UUID) -> SharedPhoto | None:
        """Find one of a User's Shared Photos.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Returns:
            The Shared Photo, or None if the User has no such photo.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(shared_photos).where(
                    shared_photos.c.user_id == user_id,
                    shared_photos.c.id == photo_id,
                )
            ).first()
        return None if row is None else _to_shared_photo(row)

    def delete_shared_photo(self, user_id: UUID, photo_id: UUID) -> bool:
        """Delete one of a User's Shared Photos.

        Args:
            user_id: The User's ID.
            photo_id: The Shared Photo's ID.

        Returns:
            True if it was deleted; False if the User has no such photo.
        """
        with self._database.begin() as connection:
            deleted = connection.execute(
                delete(shared_photos)
                .where(
                    shared_photos.c.user_id == user_id,
                    shared_photos.c.id == photo_id,
                )
                .returning(shared_photos.c.id)
            ).first()
        return deleted is not None

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Memory Items, Conversation Summaries and Shared Photos.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(memory_items).where(memory_items.c.user_id == user_id)
            )
            connection.execute(
                delete(conversation_summaries).where(
                    conversation_summaries.c.user_id == user_id
                )
            )
            connection.execute(
                delete(shared_photos).where(shared_photos.c.user_id == user_id)
            )


KNOWLEDGE_DOCUMENT_COLUMNS = [
    column for column in knowledge_documents.c if column.name not in {"content", "text"}
]


class PostgresKnowledgeDocumentRepository:
    """Stores Knowledge documents and their uploaded files in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_all(self) -> list[KnowledgeDocument]:
        """List every Knowledge document, newest upload first.

        Returns:
            The documents.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(*KNOWLEDGE_DOCUMENT_COLUMNS).order_by(
                    knowledge_documents.c.created_at.desc(),
                    knowledge_documents.c.title,
                )
            ).all()
        return [_to_knowledge_document(row) for row in rows]

    def get(self, document_id: UUID) -> KnowledgeDocument | None:
        """Find a Knowledge document.

        Args:
            document_id: The document's ID.

        Returns:
            The document, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(*KNOWLEDGE_DOCUMENT_COLUMNS).where(
                    knowledge_documents.c.id == document_id
                )
            ).first()
        return _to_knowledge_document(row) if row else None

    def get_content(self, document_id: UUID) -> bytes:
        """Read a Knowledge document's uploaded file.

        Args:
            document_id: The document's ID.

        Returns:
            The file's bytes.
        """
        with self._database.connect() as connection:
            content: bytes = connection.execute(
                select(knowledge_documents.c.content).where(
                    knowledge_documents.c.id == document_id
                )
            ).scalar_one()
        return content

    def get_text(self, document_id: UUID) -> str | None:
        """Read the text a Knowledge document's replies draw on.

        Args:
            document_id: The document's ID.

        Returns:
            The saved text, or None if none has been saved.
        """
        with self._database.connect() as connection:
            text: str | None = connection.execute(
                select(knowledge_documents.c.text).where(
                    knowledge_documents.c.id == document_id
                )
            ).scalar()
        return text

    def save_text(
        self, document_id: UUID, text: str, edited: bool
    ) -> KnowledgeDocument | None:
        """Save the text a Knowledge document's replies draw on.

        Args:
            document_id: The document's ID.
            text: The text.
            edited: Whether an Admin wrote it, rather than it being read from
                the file.

        Returns:
            The saved document, or None if it has been deleted.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(knowledge_documents)
                .where(knowledge_documents.c.id == document_id)
                .values(text=text, text_edited=edited)
                .returning(*KNOWLEDGE_DOCUMENT_COLUMNS)
            ).first()
        return _to_knowledge_document(row) if row else None

    def update_details(
        self, document_id: UUID, change: KnowledgeDetailsChange
    ) -> KnowledgeDocument | None:
        """Save new details on a Knowledge document.

        Args:
            document_id: The document's ID.
            change: The details to change; a None field is kept.

        Returns:
            The saved document, or None if there is none.
        """
        values = {
            name: value for name, value in asdict(change).items() if value is not None
        }
        if not values:
            return self.get(document_id)
        with self._database.begin() as connection:
            row = connection.execute(
                update(knowledge_documents)
                .where(knowledge_documents.c.id == document_id)
                .values(**values)
                .returning(*KNOWLEDGE_DOCUMENT_COLUMNS)
            ).first()
        return _to_knowledge_document(row) if row else None

    def replace_file(
        self, document_id: UUID, file: KnowledgeFile
    ) -> KnowledgeDocument | None:
        """Give a Knowledge document a new file and make it pending.

        Its saved text and edited flag are cleared, so the new file is read.

        Args:
            document_id: The document's ID.
            file: The new file.

        Returns:
            The saved document, or None if there is none.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(knowledge_documents)
                .where(knowledge_documents.c.id == document_id)
                .values(
                    file_name=file.file_name,
                    file_type=file.file_type.value,
                    content=file.content,
                    text=None,
                    text_edited=False,
                    status=KnowledgeStatus.PENDING.value,
                    failure_reason=None,
                )
                .returning(*KNOWLEDGE_DOCUMENT_COLUMNS)
            ).first()
        return _to_knowledge_document(row) if row else None

    def add(self, upload: KnowledgeUpload, created_at: datetime) -> KnowledgeDocument:
        """Save a new, pending Knowledge document with its file.

        Args:
            upload: The document and its file.
            created_at: When it was uploaded.

        Returns:
            The saved document.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                insert(knowledge_documents)
                .values(
                    id=uuid4(),
                    title=upload.title,
                    source=upload.source,
                    tradition=upload.tradition,
                    file_name=upload.file_name,
                    file_type=upload.file_type.value,
                    content=upload.content,
                    status=KnowledgeStatus.PENDING.value,
                    created_at=created_at,
                )
                .returning(*KNOWLEDGE_DOCUMENT_COLUMNS)
            ).one()
        return _to_knowledge_document(row)

    def set_status(
        self, document_id: UUID, status: KnowledgeStatus, failure_reason: str | None
    ) -> KnowledgeDocument | None:
        """Save where a Knowledge document is in being made ready.

        Args:
            document_id: The document's ID.
            status: Its new status.
            failure_reason: Why it failed; None unless it failed.

        Returns:
            The saved document, or None if it has been deleted.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(knowledge_documents)
                .where(knowledge_documents.c.id == document_id)
                .values(status=status.value, failure_reason=failure_reason)
                .returning(*KNOWLEDGE_DOCUMENT_COLUMNS)
            ).first()
        return _to_knowledge_document(row) if row else None

    def delete(self, document_id: UUID) -> None:
        """Remove a Knowledge document and its file.

        Args:
            document_id: The document's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(knowledge_documents).where(
                    knowledge_documents.c.id == document_id
                )
            )


class PostgresUsageRepository:
    """Stores what each User used on each day in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def claim_web_search(self, user_id: UUID, day: date, daily_limit: int) -> bool:
        """Count one web search for a User's day, in one step, if under the limit.

        Args:
            user_id: The User's ID.
            day: The User's day.
            daily_limit: The most web searches allowed in a day.

        Returns:
            True if the search was counted; False if the limit was reached,
            so two searches at once can never go over it. A refused search
            marks the web search limit reached for that day.
        """
        return self._claim(
            user_id, day, daily_limit, "web_search_count", "web_search_limit_reached"
        )

    def count_web_searches(self, user_id: UUID, day: date) -> int:
        """Count a User's web searches on a day.

        Args:
            user_id: The User's ID.
            day: The User's day.

        Returns:
            How many web searches they made.
        """
        return self._count(user_id, day, "web_search_count")

    def count_messages(self, user_id: UUID, day: date) -> int:
        """Count a User's messages on a day.

        Args:
            user_id: The User's ID.
            day: The User's day.

        Returns:
            How many of their messages counted toward the daily message limit.
        """
        return self._count(user_id, day, "message_count")

    def count_messages_on_days(self, days: Mapping[UUID, date]) -> dict[UUID, int]:
        """Count many Users' messages, each on their own day, in one query.

        Args:
            days: Each User's ID and their day.

        Returns:
            Each User's count; 0 if nothing was recorded that day.
        """
        if not days:
            return {}
        with self._database.connect() as connection:
            rows = connection.execute(
                select(daily_usage.c.user_id, daily_usage.c.message_count).where(
                    tuple_(daily_usage.c.user_id, daily_usage.c.day).in_(
                        list(days.items())
                    )
                )
            ).all()
        counts = dict.fromkeys(days, 0)
        counts |= {row.user_id: row.message_count or 0 for row in rows}
        return counts

    def _count(self, user_id: UUID, day: date, count_column: str) -> int:
        """Read one daily count for a User's day.

        Args:
            user_id: The User's ID.
            day: The User's day.
            count_column: The column holding the count.

        Returns:
            The count; 0 if nothing was recorded that day.
        """
        with self._database.connect() as connection:
            count = connection.execute(
                select(daily_usage.c[count_column]).where(
                    daily_usage.c.user_id == user_id, daily_usage.c.day == day
                )
            ).scalar()
        return count or 0

    def claim_message(self, user_id: UUID, day: date, daily_limit: int) -> bool:
        """Count one message for a User's day, in one step, if under the limit.

        Args:
            user_id: The User's ID.
            day: The User's day.
            daily_limit: The most messages allowed in a day.

        Returns:
            True if the message was counted; False if the limit was reached.
            A refused message marks the message limit reached for that day.
        """
        return self._claim(
            user_id, day, daily_limit, "message_count", "message_limit_reached"
        )

    def _claim(
        self,
        user_id: UUID,
        day: date,
        daily_limit: int,
        count_column: str,
        reached_column: str,
    ) -> bool:
        """Add one to a daily count in one step if under the limit, else mark it.

        Args:
            user_id: The User's ID.
            day: The User's day.
            daily_limit: The most allowed in a day.
            count_column: The count to add to.
            reached_column: The flag set when the limit turns one away.

        Returns:
            True if it was counted; False if the limit was reached.
        """
        count = daily_usage.c[count_column]
        key = {"user_id": user_id, "day": day}
        with self._database.begin() as connection:
            claimed = False
            if daily_limit >= 1:
                counted = connection.execute(
                    insert(daily_usage)
                    .values(**key, **{count_column: 1})
                    .on_conflict_do_update(
                        index_elements=[daily_usage.c.user_id, daily_usage.c.day],
                        set_={count_column: count + 1},
                        where=count < daily_limit,
                    )
                    .returning(count)
                ).first()
                claimed = counted is not None
            if not claimed:
                connection.execute(
                    insert(daily_usage)
                    .values(**key, **{reached_column: True})
                    .on_conflict_do_update(
                        index_elements=[daily_usage.c.user_id, daily_usage.c.day],
                        set_={reached_column: True},
                    )
                )
        return claimed

    def add_tokens(
        self, user_id: UUID, day: date, tokens_in: int, tokens_out: int
    ) -> None:
        """Add chat model tokens to a User's day.

        Args:
            user_id: The User's ID.
            day: The User's day.
            tokens_in: Tokens the model read.
            tokens_out: Tokens the model wrote.
        """
        statement = insert(daily_usage).values(
            user_id=user_id, day=day, tokens_in=tokens_in, tokens_out=tokens_out
        )
        with self._database.begin() as connection:
            connection.execute(
                statement.on_conflict_do_update(
                    index_elements=[daily_usage.c.user_id, daily_usage.c.day],
                    set_={
                        "tokens_in": daily_usage.c.tokens_in + tokens_in,
                        "tokens_out": daily_usage.c.tokens_out + tokens_out,
                    },
                )
            )

    def list_since(self, first_day: date) -> list[DailyUsage]:
        """List every User's usage from a day on.

        Args:
            first_day: The earliest day to list.

        Returns:
            One entry per User per day, newest day first, then by User.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(
                    daily_usage,
                    users.c.name.label("user_name"),
                    users.c.email.label("user_email"),
                    users.c.time_zone.label("user_time_zone"),
                )
                .join(users, users.c.id == daily_usage.c.user_id)
                .where(daily_usage.c.day >= first_day)
                .order_by(
                    daily_usage.c.day.desc(),
                    func.lower(func.coalesce(users.c.name, users.c.email)),
                    users.c.id,
                )
            ).all()
        return [
            DailyUsage(
                day=row.day,
                user_id=row.user_id,
                user_name=row.user_name,
                user_email=row.user_email,
                user_time_zone=row.user_time_zone,
                message_count=row.message_count,
                tokens_in=row.tokens_in,
                tokens_out=row.tokens_out,
                web_search_count=row.web_search_count,
                message_limit_reached=row.message_limit_reached,
                web_search_limit_reached=row.web_search_limit_reached,
            )
            for row in rows
        ]

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Usage.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(daily_usage).where(daily_usage.c.user_id == user_id)
            )


class PostgresStickerRepository:
    """Stores the Sticker Library in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_all(self) -> list[LibrarySticker]:
        """List every sticker in the order they were added.

        Returns:
            The stickers.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(stickers).order_by(stickers.c.position)
            ).all()
        return [_to_library_sticker(row) for row in rows]

    def get(self, sticker_id: UUID) -> LibrarySticker | None:
        """Find a sticker.

        Args:
            sticker_id: The sticker's ID.

        Returns:
            The sticker, or None if there is none.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(stickers).where(stickers.c.id == sticker_id)
            ).first()
        return _to_library_sticker(row) if row else None

    def add_new(self, new_stickers: list[ChannelSticker], added_at: datetime) -> int:
        """Add stickers without a note, skipping any already in the library.

        Args:
            new_stickers: The stickers, in order.
            added_at: When they are being added.

        Returns:
            How many were added.
        """
        if not new_stickers:
            return 0
        rows = [
            {
                "id": uuid4(),
                "file_id": sticker.file_id,
                "file_unique_id": sticker.file_unique_id,
                "emoji": sticker.emoji,
                "set_name": sticker.set_name,
                "preview_file_id": sticker.preview_file_id,
                "note": "",
                "added_at": added_at,
            }
            for sticker in new_stickers
        ]
        with self._database.begin() as connection:
            added = connection.execute(
                insert(stickers)
                .values(rows)
                .on_conflict_do_nothing(index_elements=[stickers.c.file_unique_id])
                .returning(stickers.c.id)
            ).all()
        return len(added)

    def save_note(self, sticker_id: UUID, note: str) -> LibrarySticker | None:
        """Save a sticker's "when to use" note.

        Args:
            sticker_id: The sticker's ID.
            note: The note.

        Returns:
            The saved sticker, or None if there is none.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(stickers)
                .where(stickers.c.id == sticker_id)
                .values(note=note)
                .returning(stickers)
            ).first()
        return _to_library_sticker(row) if row else None

    def delete(self, sticker_id: UUID) -> bool:
        """Remove a sticker.

        Args:
            sticker_id: The sticker's ID.

        Returns:
            True if it was removed; False if there was none.
        """
        with self._database.begin() as connection:
            removed = connection.execute(
                delete(stickers)
                .where(stickers.c.id == sticker_id)
                .returning(stickers.c.id)
            ).first()
        return removed is not None


class PostgresPersonalStickerRepository:
    """Stores the stickers kept from each User in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_for_user(self, user_id: UUID) -> list[PersonalSticker]:
        """List a User's Personal Stickers, most recently used first.

        Args:
            user_id: The User.

        Returns:
            The stickers.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(personal_stickers)
                .where(personal_stickers.c.user_id == user_id)
                .order_by(
                    personal_stickers.c.last_used_at.desc(), personal_stickers.c.id
                )
            ).all()
        return [_to_personal_sticker(row) for row in rows]

    def get(self, user_id: UUID, sticker_id: UUID) -> PersonalSticker | None:
        """Find one of a User's Personal Stickers.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Returns:
            The sticker, or None if the User has none with that ID.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(personal_stickers).where(
                    personal_stickers.c.user_id == user_id,
                    personal_stickers.c.id == sticker_id,
                )
            ).first()
        return _to_personal_sticker(row) if row else None

    def save_many(self, stickers: list[PersonalSticker]) -> None:
        """Keep stickers, replacing the User's own copy of the same sticker.

        A sticker the User already has, by its unchanging ID, keeps its ID,
        when it was first kept and its later last use; the rest is replaced.

        Args:
            stickers: The stickers to keep.
        """
        if not stickers:
            return
        statement = insert(personal_stickers).values(
            [asdict(sticker) for sticker in stickers]
        )
        with self._database.begin() as connection:
            connection.execute(
                statement.on_conflict_do_update(
                    index_elements=[
                        personal_stickers.c.user_id,
                        personal_stickers.c.file_unique_id,
                    ],
                    set_={
                        "file_id": statement.excluded.file_id,
                        "emoji": statement.excluded.emoji,
                        "set_name": statement.excluded.set_name,
                        "preview_file_id": statement.excluded.preview_file_id,
                        "note": statement.excluded.note,
                        "last_used_at": func.greatest(
                            personal_stickers.c.last_used_at,
                            statement.excluded.last_used_at,
                        ),
                    },
                )
            )

    def mark_used(self, user_id: UUID, sticker_id: UUID, used_at: datetime) -> None:
        """Note that one of a User's Personal Stickers was just sent.

        Args:
            user_id: The User it belongs to.
            sticker_id: The sticker's ID.
            used_at: When it was sent.
        """
        with self._database.begin() as connection:
            connection.execute(
                update(personal_stickers)
                .where(
                    personal_stickers.c.user_id == user_id,
                    personal_stickers.c.id == sticker_id,
                )
                .values(last_used_at=used_at)
            )

    def keep_most_recently_used(self, user_id: UUID, limit: int) -> None:
        """Drop a User's Personal Stickers used longest ago, beyond a limit.

        Args:
            user_id: The User.
            limit: How many to keep.
        """
        kept_ids = (
            select(personal_stickers.c.id)
            .where(personal_stickers.c.user_id == user_id)
            .order_by(personal_stickers.c.last_used_at.desc(), personal_stickers.c.id)
            .limit(limit)
        )
        with self._database.begin() as connection:
            connection.execute(
                delete(personal_stickers).where(
                    personal_stickers.c.user_id == user_id,
                    personal_stickers.c.id.not_in(kept_ids),
                )
            )

    def delete(self, user_id: UUID, sticker_id: UUID) -> bool:
        """Remove one of a User's Personal Stickers.

        Args:
            user_id: The User it must belong to.
            sticker_id: The sticker's ID.

        Returns:
            True if it was removed; False if the User had none with that ID.
        """
        with self._database.begin() as connection:
            removed = connection.execute(
                delete(personal_stickers)
                .where(
                    personal_stickers.c.user_id == user_id,
                    personal_stickers.c.id == sticker_id,
                )
                .returning(personal_stickers.c.id)
            ).first()
        return removed is not None

    def count_for_user(self, user_id: UUID) -> int:
        """Count a User's Personal Stickers.

        Args:
            user_id: The User.

        Returns:
            How many they have.
        """
        with self._database.connect() as connection:
            count: int = connection.execute(
                select(func.count())
                .select_from(personal_stickers)
                .where(personal_stickers.c.user_id == user_id)
            ).scalar_one()
        return count

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Personal Stickers.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(personal_stickers).where(personal_stickers.c.user_id == user_id)
            )


class PostgresCheckInRepository:
    """Stores Check-in Kinds and Check-in decisions in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_kinds(self) -> list[CheckInKind]:
        """List every Check-in Kind in order.

        Returns:
            The Check-in Kinds.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                select(check_in_kinds).order_by(check_in_kinds.c.sort_order)
            ).all()
        return [_to_check_in_kind(row) for row in rows]

    def list_kind_overviews(self, sent_since: datetime) -> list[CheckInKindOverview]:
        """List every Check-in Kind in order with how often it was sent lately.

        Args:
            sent_since: Only Check-ins sent after this are counted.

        Returns:
            The Check-in Kinds with their send counts.
        """
        sent_count = func.count(check_ins.c.id).label("sent_count")
        with self._database.connect() as connection:
            rows = connection.execute(
                select(check_in_kinds, sent_count)
                .outerjoin(
                    check_ins,
                    (check_ins.c.kind_id == check_in_kinds.c.id)
                    & (check_ins.c.decided_at > sent_since),
                )
                .group_by(check_in_kinds.c.id)
                .order_by(check_in_kinds.c.sort_order)
            ).all()
        return [
            CheckInKindOverview(kind=_to_check_in_kind(row), sent_count=row.sent_count)
            for row in rows
        ]

    def get_kind(self, kind_id: UUID) -> CheckInKind | None:
        """Find one Check-in Kind.

        Args:
            kind_id: The Check-in Kind's ID.

        Returns:
            The Check-in Kind, or None if there is no such Kind.
        """
        with self._database.connect() as connection:
            row = connection.execute(
                select(check_in_kinds).where(check_in_kinds.c.id == kind_id)
            ).first()
        return _to_check_in_kind(row) if row else None

    def add_kind(self, details: CheckInKindDetails) -> CheckInKind:
        """Add a Check-in Kind last in the list.

        Args:
            details: Its name and description.

        Returns:
            The saved Check-in Kind.
        """
        with self._database.begin() as connection:
            highest = connection.execute(
                select(func.max(check_in_kinds.c.sort_order))
            ).scalar()
            row = connection.execute(
                insert(check_in_kinds)
                .values(
                    id=uuid4(),
                    name=details.name,
                    description=details.description,
                    sort_order=0 if highest is None else int(highest) + 1,
                    sends_shared_photo=False,
                )
                .returning(check_in_kinds)
            ).one()
        return _to_check_in_kind(row)

    def update_kind(self, kind: CheckInKind) -> CheckInKind:
        """Save a Check-in Kind's name and description.

        Args:
            kind: The Check-in Kind with its new values.

        Returns:
            The saved Check-in Kind.
        """
        with self._database.begin() as connection:
            row = connection.execute(
                update(check_in_kinds)
                .where(check_in_kinds.c.id == kind.id)
                .values(name=kind.name, description=kind.description)
                .returning(check_in_kinds)
            ).one()
        return _to_check_in_kind(row)

    def delete_kind(self, kind_id: UUID) -> bool:
        """Remove a Check-in Kind; past Check-ins of it keep no Kind.

        Args:
            kind_id: The Check-in Kind's ID.

        Returns:
            True if it was removed; False if there was no such Kind.
        """
        with self._database.begin() as connection:
            deleted = connection.execute(
                delete(check_in_kinds)
                .where(check_in_kinds.c.id == kind_id)
                .returning(check_in_kinds.c.id)
            ).first()
        return deleted is not None

    def list_due_users(self, now: datetime) -> list[User]:
        """List onboarded Users with Check-ins on whose next one is due.

        Users whose Check-ins are off on the Admin side, for everyone or for
        them, are left out but stay due.

        Args:
            now: The time to check at.

        Returns:
            The Users whose next due time is at or before now; a User with no
            due time is never due.
        """
        check_ins_feature = Feature.CHECK_INS.value
        admin_side_on = func.coalesce(
            user_feature_switches.c.is_on,
            feature_switches.c.is_on,
            feature_details(Feature.CHECK_INS).on_by_default,
        )
        statement = (
            select(users)
            .select_from(
                users.outerjoin(
                    user_feature_switches,
                    and_(
                        user_feature_switches.c.user_id == users.c.id,
                        user_feature_switches.c.feature == check_ins_feature,
                    ),
                ).outerjoin(
                    feature_switches, feature_switches.c.feature == check_ins_feature
                )
            )
            .where(
                users.c.check_ins_enabled.is_(True),
                users.c.onboarding_completed_at.is_not(None),
                users.c.check_in_next_due_at <= now,
                admin_side_on.is_(True),
            )
        )
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [_to_user(row) for row in rows]

    def save_next_due_times(self, changes: Sequence[NextDueTimeChange]) -> None:
        """Save many Users' next due times, in one statement.

        A User whose due time changed since it was read is left as it is, so
        a settings change made meanwhile is kept.

        Args:
            changes: Each User's due time as read and the one to save.
        """
        if not changes:
            return
        due_type = users.c.check_in_next_due_at.type
        statement = (
            update(users)
            .where(
                users.c.id == bindparam("changed_user_id"),
                users.c.check_in_next_due_at.is_not_distinct_from(
                    bindparam("read_as", type_=due_type)
                ),
            )
            .values(check_in_next_due_at=bindparam("becomes", type_=due_type))
        )
        with self._database.begin() as connection:
            connection.execute(
                statement,
                [
                    {
                        "changed_user_id": change.user_id,
                        "read_as": change.read_as,
                        "becomes": change.becomes,
                    }
                    for change in changes
                ],
            )

    def set_due_now_unless_due_later(self, user_id: UUID, now: datetime) -> None:
        """Make a User with Check-ins on due now, unless they are due later.

        A due time of now also wins over a tick that read the old one and is
        holding the User back meanwhile.

        Args:
            user_id: The User's ID.
            now: The current time.
        """
        with self._database.begin() as connection:
            connection.execute(
                update(users)
                .where(
                    users.c.id == user_id,
                    users.c.check_ins_enabled.is_(True),
                    or_(
                        users.c.check_in_next_due_at.is_(None),
                        users.c.check_in_next_due_at <= now,
                    ),
                )
                .values(check_in_next_due_at=now)
            )

    def add(
        self, check_in: CheckIn, next_due_at: datetime, pause_until_resumed: bool
    ) -> None:
        """Save a Check-in decision and the User's next due time, together.

        Args:
            check_in: The Check-in decision.
            next_due_at: When the User's next Check-in may be sent.
            pause_until_resumed: Whether to also pause the User's Check-ins
                until they resume.
        """
        user_changes: dict[str, Any] = {"check_in_next_due_at": next_due_at}
        if pause_until_resumed:
            user_changes |= {"check_ins_paused": True, "check_ins_paused_until": None}
        with self._database.begin() as connection:
            self._insert(connection, check_in)
            connection.execute(
                update(users)
                .where(users.c.id == check_in.user_id)
                .values(**user_changes)
            )

    def undo_add(
        self,
        check_in: CheckIn,
        next_due_at: datetime,
        end_pause: bool,
        skipped: CheckIn | None,
    ) -> None:
        """Take back a saved Check-in that was never sent, together.

        Args:
            check_in: The saved Check-in to remove.
            next_due_at: When the User's next Check-in may be sent.
            end_pause: Whether to end the pause that saving it started.
            skipped: A Skipped Check-in to save in its place; None for none.
        """
        user_changes: dict[str, Any] = {"check_in_next_due_at": next_due_at}
        if end_pause:
            user_changes |= {"check_ins_paused": False, "check_ins_paused_until": None}
        with self._database.begin() as connection:
            connection.execute(delete(check_ins).where(check_ins.c.id == check_in.id))
            if skipped is not None:
                self._insert(connection, skipped)
            connection.execute(
                update(users)
                .where(users.c.id == check_in.user_id)
                .values(**user_changes)
            )

    def remove_shared_photo(self, check_in_id: UUID) -> None:
        """Mark a sent Check-in as having sent no Shared Photo.

        Args:
            check_in_id: The Check-in's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                update(check_ins)
                .where(check_ins.c.id == check_in_id)
                .values(shared_photo_id=None)
            )

    def list_recent(self, user_id: UUID, limit: int) -> list[CheckIn]:
        """List a User's newest Check-in decisions, newest first.

        Args:
            user_id: The User's ID.
            limit: The most to list.

        Returns:
            The Check-ins.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                self._select_check_ins()
                .where(check_ins.c.user_id == user_id)
                .order_by(check_ins.c.decided_at.desc())
                .limit(limit)
            ).all()
        return [self._to_check_in(row) for row in rows]

    def list_recent_for_users(
        self, user_ids: Sequence[UUID], limit: int, sent_only: bool
    ) -> dict[UUID, list[CheckIn]]:
        """List many Users' newest Check-in decisions, in one query.

        Args:
            user_ids: The Users' IDs.
            limit: The most to list per User.
            sent_only: Whether to leave out Skipped Check-ins.

        Returns:
            Each User's Check-ins, newest first; a User with none is left out.
        """
        newest_first = func.row_number().over(
            partition_by=check_ins.c.user_id, order_by=check_ins.c.decided_at.desc()
        )
        ranked = (
            self._select_check_ins()
            .add_columns(newest_first.label("place"))
            .where(check_ins.c.user_id.in_(user_ids))
        )
        if sent_only:
            ranked = ranked.where(check_ins.c.outcome != CheckInOutcome.SKIPPED.value)
        ranked_check_ins = ranked.subquery()
        with self._database.connect() as connection:
            rows = connection.execute(
                select(ranked_check_ins)
                .where(ranked_check_ins.c.place <= limit)
                .order_by(ranked_check_ins.c.user_id, ranked_check_ins.c.place)
            ).all()
        recent_by_user: dict[UUID, list[CheckIn]] = {}
        for row in rows:
            recent_by_user.setdefault(row.user_id, []).append(self._to_check_in(row))
        return recent_by_user

    def list_log(self, since: datetime) -> list[CheckInLogEntry]:
        """List every User's Check-in decisions since a time, newest first.

        Args:
            since: Only decisions after this are listed.

        Returns:
            The decisions with who each User is.
        """
        with self._database.connect() as connection:
            rows = connection.execute(
                self._select_check_ins()
                .add_columns(
                    users.c.name.label("user_name"), users.c.email.label("user_email")
                )
                .join(users, users.c.id == check_ins.c.user_id)
                .where(check_ins.c.decided_at > since)
                .order_by(check_ins.c.decided_at.desc())
            ).all()
        return [
            CheckInLogEntry(
                check_in=self._to_check_in(row),
                user_name=row.user_name,
                user_email=row.user_email,
            )
            for row in rows
        ]

    def claim_reply(
        self, user_id: UUID, replied_at: datetime, sent_since: datetime
    ) -> CheckIn | None:
        """Mark the User's newest sent Check-in replied, if it can still be.

        Args:
            user_id: The User's ID.
            replied_at: When they replied.
            sent_since: A Check-in sent at or before this can't get a reply.

        Returns:
            The Check-in they replied to, or None if their newest sent
            Check-in was already replied to, was sent before `sent_since`, or
            they have none.
        """
        newest_id = (
            select(check_ins.c.id)
            .where(
                check_ins.c.user_id == user_id,
                check_ins.c.outcome != CheckInOutcome.SKIPPED.value,
            )
            .order_by(check_ins.c.decided_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        with self._database.begin() as connection:
            claimed_id = connection.execute(
                update(check_ins)
                .where(
                    check_ins.c.id == newest_id,
                    check_ins.c.replied_at.is_(None),
                    check_ins.c.decided_at > sent_since,
                )
                .values(replied_at=replied_at)
                .returning(check_ins.c.id)
            ).scalar()
            if claimed_id is None:
                return None
            row = connection.execute(
                self._select_check_ins().where(check_ins.c.id == claimed_id)
            ).one()
        return self._to_check_in(row)

    @staticmethod
    def _insert(connection: Connection, check_in: CheckIn) -> None:
        """Save one Check-in decision on an open connection.

        Args:
            connection: The connection, inside a transaction.
            check_in: The Check-in decision.
        """
        connection.execute(
            insert(check_ins).values(
                id=check_in.id,
                user_id=check_in.user_id,
                outcome=check_in.outcome.value,
                kind_id=check_in.kind_id,
                message=check_in.message,
                skip_reason=check_in.skip_reason,
                decided_at=check_in.decided_at,
                replied_at=check_in.replied_at,
                shared_photo_id=check_in.shared_photo_id,
            )
        )

    @staticmethod
    def _select_check_ins() -> Select[Any]:
        """Select Check-ins with their Check-in Kind's name.

        Returns:
            The select statement.
        """
        return select(check_ins, check_in_kinds.c.name.label("kind_name")).join(
            check_in_kinds, check_ins.c.kind_id == check_in_kinds.c.id, isouter=True
        )

    @staticmethod
    def _to_check_in(row: Row[Any]) -> CheckIn:
        """Turn a Check-in row with its Kind's name into a CheckIn.

        Args:
            row: The database row.

        Returns:
            The Check-in.
        """
        return CheckIn(
            id=row.id,
            user_id=row.user_id,
            outcome=CheckInOutcome(row.outcome),
            decided_at=row.decided_at,
            kind_id=row.kind_id,
            kind_name=row.kind_name,
            message=row.message,
            skip_reason=row.skip_reason,
            replied_at=row.replied_at,
            shared_photo_id=row.shared_photo_id,
        )

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's Check-in history.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(delete(check_ins).where(check_ins.c.user_id == user_id))


class PostgresFeatureSwitchRepository:
    """Stores each Feature's switches, for everyone and per User, in Postgres."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def list_for_everyone(self) -> list[FeatureSwitch]:
        """List the stored switches for everyone.

        Returns:
            The switches that are stored, in no set order.
        """
        statement = select(
            feature_switches.c.feature,
            feature_switches.c.is_on,
            feature_switches.c.changed_at,
            users.c.email,
        ).select_from(feature_switches.outerjoin(users))
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [
            FeatureSwitch(
                feature=Feature(row.feature),
                on=row.is_on,
                changed_by_email=row.email,
                changed_at=row.changed_at,
            )
            for row in rows
            if row.feature in Feature
        ]

    def save_for_everyone(
        self, feature: Feature, on: bool, changed_at: datetime, changed_by: UUID
    ) -> None:
        """Save a Feature's switch for everyone.

        Args:
            feature: The Feature.
            on: Whether it is on for everyone.
            changed_at: When it is being changed.
            changed_by: The Admin changing it.
        """
        values = {"is_on": on, "changed_at": changed_at, "changed_by": changed_by}
        with self._database.begin() as connection:
            connection.execute(
                insert(feature_switches)
                .values(feature=feature.value, **values)
                .on_conflict_do_update(index_elements=["feature"], set_=values)
            )

    def list_for_user(self, user_id: UUID) -> list[FeatureSwitch]:
        """List the switches stored for one User.

        Only switches set to "on" or "off" are stored.

        Args:
            user_id: The User.

        Returns:
            The User's switches, in no set order.
        """
        return self.list_for_users([user_id]).get(user_id, [])

    def list_for_users(
        self, user_ids: Sequence[UUID]
    ) -> dict[UUID, list[FeatureSwitch]]:
        """List the switches stored for many Users, in one query.

        Args:
            user_ids: The Users.

        Returns:
            Each User's switches, in no set order; a User with none is left
            out.
        """
        statement = (
            select(
                user_feature_switches.c.user_id,
                user_feature_switches.c.feature,
                user_feature_switches.c.is_on,
                user_feature_switches.c.changed_at,
                users.c.email,
            )
            .select_from(
                user_feature_switches.outerjoin(
                    users, users.c.id == user_feature_switches.c.changed_by
                )
            )
            .where(user_feature_switches.c.user_id.in_(user_ids))
        )
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        switches_by_user: dict[UUID, list[FeatureSwitch]] = {}
        for row in rows:
            if row.feature in Feature:
                switches_by_user.setdefault(row.user_id, []).append(
                    FeatureSwitch(
                        feature=Feature(row.feature),
                        on=row.is_on,
                        changed_by_email=row.email,
                        changed_at=row.changed_at,
                    )
                )
        return switches_by_user

    def save_for_user(
        self,
        user_id: UUID,
        feature: Feature,
        on: bool,
        changed_at: datetime,
        changed_by: UUID,
    ) -> None:
        """Save a Feature's switch for one User as on or off.

        Args:
            user_id: The User.
            feature: The Feature.
            on: Whether it is on for the User.
            changed_at: When it is being changed.
            changed_by: The Admin changing it.
        """
        values = {"is_on": on, "changed_at": changed_at, "changed_by": changed_by}
        with self._database.begin() as connection:
            connection.execute(
                insert(user_feature_switches)
                .values(user_id=user_id, feature=feature.value, **values)
                .on_conflict_do_update(
                    index_elements=["user_id", "feature"], set_=values
                )
            )

    def remove_for_user(self, user_id: UUID, feature: Feature) -> None:
        """Remove a Feature's switch for one User, so it follows everyone's.

        Args:
            user_id: The User.
            feature: The Feature.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(user_feature_switches).where(
                    user_feature_switches.c.user_id == user_id,
                    user_feature_switches.c.feature == feature.value,
                )
            )

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's own Feature Switches.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(user_feature_switches).where(
                    user_feature_switches.c.user_id == user_id
                )
            )


class _TransactionConnection:
    """Lends every repository the one connection of an open transaction."""

    def __init__(self, connection: Connection) -> None:
        """Set up the lender.

        Args:
            connection: The transaction's connection.
        """
        self._connection = connection

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        """Lend the transaction's connection, leaving it open.

        Yields:
            The connection.
        """
        yield self._connection

    def begin(self) -> AbstractContextManager[Connection]:
        """Lend the transaction's connection; its changes are saved with the rest.

        Returns:
            The connection, as a context manager.
        """
        return self.connect()


class PostgresTransaction:
    """One Postgres transaction across every repository."""

    def __init__(self, connection: Connection) -> None:
        """Set up the transaction.

        Args:
            connection: The connection the transaction runs on.
        """
        self._connection = connection
        self._repositories = _build_repositories(
            _TransactionConnection(connection), self._join
        )

    @property
    def repositories(self) -> Repositories:
        """The repositories, each working inside this transaction."""
        return self._repositories

    def lock_admins(self) -> list[UUID]:
        """Lock the Admin rows until the transaction ends, and list them.

        Rows are locked in ID order, so two transactions locking them never
        deadlock.

        Returns:
            The IDs of the Users who are Admins.
        """
        return list(
            self._connection.execute(
                select(users.c.id)
                .where(users.c.role == UserRole.ADMIN.value)
                .order_by(users.c.id)
                .with_for_update()
            ).scalars()
        )

    @contextmanager
    def _join(self) -> Iterator["PostgresTransaction"]:
        """Join this transaction, for a transaction started inside it.

        Yields:
            This transaction.
        """
        yield self


@contextmanager
def _begin_transaction(engine: Engine) -> Iterator[Transaction]:
    """Start a transaction, saved when the block ends and undone if it fails.

    Args:
        engine: The database engine.

    Yields:
        The transaction.
    """
    with engine.begin() as connection:
        yield PostgresTransaction(connection)


def build_postgres_repositories(engine: Engine) -> Repositories:
    """Build every repository on one Postgres engine.

    Args:
        engine: The database engine.

    Returns:
        The repositories.
    """
    return _build_repositories(engine, partial(_begin_transaction, engine))


def _to_model_call_content(values: dict[str, Any]) -> ModelCallContent:
    """Read a model call's stored content.

    Args:
        values: The stored JSON.

    Returns:
        The content.
    """
    return ModelCallContent(
        instructions=values["instructions"],
        history=tuple(
            ChatLine(role=ChatRole(line["role"]), text=line["text"])
            for line in values["history"]
        ),
        tools_offered=tuple(OfferedTool(**tool) for tool in values["tools_offered"]),
        tool_calls=tuple(ToolCallRecord(**call) for call in values["tool_calls"]),
        response=values["response"],
        reasoning=values["reasoning"],
    )


def _to_model_call(row: Row[Any]) -> ModelCall:
    """Turn a `model_calls` row into a model call.

    Args:
        row: The row.

    Returns:
        The model call.
    """
    return ModelCall(
        id=row.id,
        trace=ModelCallTrace(id=row.trace_id, kind=TraceKind(row.trace_kind)),
        user_id=row.user_id,
        step=ModelStep(row.step),
        model=row.model,
        started_at=row.started_at,
        duration_ms=row.duration_ms,
        tokens_in=row.tokens_in,
        tokens_out=row.tokens_out,
        error=row.error,
        tools_called=tuple(row.tools_called),
        content=_to_model_call_content(row.content) if row.content else None,
    )


class PostgresModelCallRepository:
    """Stores the Model Call Log in Postgres, one row per model call."""

    def __init__(self, database: Database) -> None:
        """Set up the repository.

        Args:
            database: Where to run queries: the engine, or one transaction.
        """
        self._database = database

    def add(self, call: ModelCall) -> None:
        """Save one model call.

        Args:
            call: The call to save.
        """
        with self._database.begin() as connection:
            connection.execute(
                insert(model_calls).values(
                    id=call.id,
                    trace_id=call.trace.id,
                    trace_kind=call.trace.kind.value,
                    user_id=call.user_id,
                    step=call.step.value,
                    model=call.model,
                    started_at=call.started_at,
                    duration_ms=call.duration_ms,
                    tokens_in=call.tokens_in,
                    tokens_out=call.tokens_out,
                    error=call.error,
                    tools_called=list(call.tools_called),
                    content=asdict(call.content) if call.content else None,
                )
            )

    def list_traces(
        self,
        user_id: UUID | None,
        since: datetime | None,
        step: ModelStep | None,
        errors_only: bool,
        limit: int,
    ) -> list[ModelCallTraceOverview]:
        """List traces with who they were for, newest first.

        Args:
            user_id: Only this User's traces; None for every User.
            since: Only traces started at or after this time; None for all time.
            step: Only traces with a call for this step; None for every step.
            errors_only: Only traces with a failed call.
            limit: The most traces to list.

        Returns:
            The traces.
        """
        started_at = func.min(model_calls.c.started_at)
        error_count = func.count(model_calls.c.error)
        statement = (
            self._trace_overview_select().order_by(started_at.desc()).limit(limit)
        )
        if user_id is not None:
            statement = statement.where(model_calls.c.user_id == user_id)
        if since is not None:
            statement = statement.having(started_at >= since)
        if step is not None:
            statement = statement.having(func.bool_or(model_calls.c.step == step.value))
        if errors_only:
            statement = statement.having(error_count > 0)
        with self._database.connect() as connection:
            rows = connection.execute(statement).all()
        return [self._to_trace_overview(row) for row in rows]

    def get_trace(self, trace_id: UUID) -> ModelCallTraceDetails | None:
        """Read one trace with every call in it.

        Args:
            trace_id: The trace's ID.

        Returns:
            The trace, or None if there is no such trace.
        """
        with self._database.connect() as connection:
            overview_row = connection.execute(
                self._trace_overview_select().where(model_calls.c.trace_id == trace_id)
            ).one_or_none()
            if overview_row is None:
                return None
            call_rows = connection.execute(
                select(model_calls)
                .where(model_calls.c.trace_id == trace_id)
                .order_by(model_calls.c.position)
            ).all()
        return ModelCallTraceDetails(
            overview=self._to_trace_overview(overview_row),
            calls=tuple(_to_model_call(row) for row in call_rows),
        )

    def delete_started_before(self, cutoff: datetime) -> None:
        """Delete every call that started before a time.

        Args:
            cutoff: Calls that started before this are deleted.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(model_calls).where(model_calls.c.started_at < cutoff)
            )

    def delete_for_user(self, user_id: UUID) -> None:
        """Delete a User's calls.

        Args:
            user_id: The User's ID.
        """
        with self._database.begin() as connection:
            connection.execute(
                delete(model_calls).where(model_calls.c.user_id == user_id)
            )

    @staticmethod
    def _trace_overview_select() -> Select[Any]:
        """Build the query that sums each trace's calls, with who it was for.

        Returns:
            The query, grouped by trace.
        """
        return (
            select(
                model_calls.c.trace_id,
                model_calls.c.trace_kind,
                model_calls.c.user_id,
                users.c.name.label("user_name"),
                users.c.email.label("user_email"),
                func.min(model_calls.c.started_at).label("started_at"),
                func.array_agg(
                    aggregate_order_by(model_calls.c.step, model_calls.c.position)
                ).label("steps"),
                func.sum(model_calls.c.tokens_in).label("tokens_in"),
                func.sum(model_calls.c.tokens_out).label("tokens_out"),
                func.sum(model_calls.c.duration_ms).label("duration_ms"),
                func.count(model_calls.c.error).label("error_count"),
                func.bool_or(model_calls.c.content.is_not(None)).label("has_content"),
            )
            .select_from(model_calls.join(users))
            .group_by(
                model_calls.c.trace_id,
                model_calls.c.trace_kind,
                model_calls.c.user_id,
                users.c.name,
                users.c.email,
            )
        )

    @staticmethod
    def _to_trace_overview(row: Row[Any]) -> ModelCallTraceOverview:
        """Turn a summed trace row into a trace overview.

        Args:
            row: The row from `_trace_overview_select`.

        Returns:
            The trace overview.
        """
        return ModelCallTraceOverview(
            trace=ModelCallTrace(id=row.trace_id, kind=TraceKind(row.trace_kind)),
            user_id=row.user_id,
            user_name=row.user_name,
            user_email=row.user_email,
            started_at=row.started_at,
            steps=tuple(ModelStep(step) for step in row.steps),
            tokens_in=row.tokens_in,
            tokens_out=row.tokens_out,
            duration_ms=row.duration_ms,
            error_count=row.error_count,
            has_content=row.has_content,
        )


def _build_repositories(
    database: Database,
    transaction: Callable[[], AbstractContextManager[Transaction]],
) -> Repositories:
    """Build every repository on one database.

    Args:
        database: Where to run queries: the engine, or one transaction.
        transaction: Starts a transaction across the repositories.

    Returns:
        The repositories.
    """
    return Repositories(
        users=PostgresUserRepository(database),
        telegram_connections=PostgresTelegramConnectionRepository(database),
        connection_tokens=PostgresConnectionTokenRepository(database),
        conversations=PostgresConversationRepository(database),
        platform_settings=PostgresPlatformSettingsRepository(database),
        helplines=PostgresHelplineRepository(database),
        safeguard_events=PostgresSafeguardEventRepository(database),
        memory_categories=PostgresMemoryCategoryRepository(database),
        needs=PostgresNeedRepository(database),
        understandings=PostgresUnderstandingRepository(database),
        user_memory=PostgresUserMemoryRepository(database),
        knowledge_documents=PostgresKnowledgeDocumentRepository(database),
        usage=PostgresUsageRepository(database),
        stickers=PostgresStickerRepository(database),
        personal_stickers=PostgresPersonalStickerRepository(database),
        check_ins=PostgresCheckInRepository(database),
        feature_switches=PostgresFeatureSwitchRepository(database),
        pending_auth_account_deletions=PostgresPendingAuthAccountDeletionRepository(
            database
        ),
        model_calls=PostgresModelCallRepository(database),
        transaction=transaction,
    )
