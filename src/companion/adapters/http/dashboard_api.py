from collections.abc import Callable
from datetime import datetime, time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from companion.core.check_ins import CheckInService, RecentCheckIn
from companion.core.features import FeatureNotAvailableError, FeatureService
from companion.core.home import Home, HomeService
from companion.core.message_retention import RETENTION_DAYS_SETTING
from companion.core.models import (
    ChatSetting,
    CheckInChanges,
    CheckInFrequency,
    CheckInOutcome,
    CheckInSettings,
    CheckInStatus,
    ConnectionToken,
    ConnectionTokenStatus,
    ConversationSummary,
    Feature,
    MemoryGroup,
    MemoryItem,
    MemorySource,
    OnboardingAnswers,
    PauseLength,
    PersonalSticker,
    PreferenceChanges,
    SharedPhoto,
    User,
    UserRole,
)
from companion.core.personal_stickers import (
    PersonalStickerNotFoundError,
    PersonalStickerService,
)
from companion.core.photos import PhotoService, SharedPhotoNotFoundError
from companion.core.ports import PlatformSettingsRepository
from companion.core.telegram_connection import (
    OnboardingNotFinishedError,
    TelegramConnectionService,
)
from companion.core.user_data import LastAdminError, UserDataService
from companion.core.user_memory import MemoryNotFoundError, UserMemoryService
from companion.core.users import InvalidProfileError, UserService


class MeResponse(BaseModel):
    """The signed-in User, with their profile and preferences."""

    id: str
    email: str | None
    name: str | None
    onboarding_reasons: list[str]
    onboarding_note: str | None
    country: str | None
    time_zone: str | None
    ai_notice_acknowledged_at: datetime | None
    user_memory_enabled: bool
    user_memory_available: bool
    photo_viewing_enabled: bool
    photo_viewing_available: bool
    personal_stickers_available: bool
    onboarding_completed_at: datetime | None
    role: UserRole
    changed_in_chat: dict[ChatSetting, datetime]


DEFAULT_CHECK_INS = CheckInSettings()
NOT_AVAILABLE = "Not available on your account"


class OnboardingRequest(BaseModel):
    """Everything a new User answers during onboarding."""

    name: str
    ai_notice_acknowledged: bool
    onboarding_reasons: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list, max_length=20
    )
    onboarding_note: str | None = Field(default=None, max_length=2000)
    user_memory_enabled: bool
    country: str
    time_zone: str
    check_ins_enabled: bool = DEFAULT_CHECK_INS.enabled
    check_in_frequency: CheckInFrequency = DEFAULT_CHECK_INS.frequency
    quiet_hours_start: time = DEFAULT_CHECK_INS.quiet_hours_start
    quiet_hours_end: time = DEFAULT_CHECK_INS.quiet_hours_end


class PreferencesRequest(BaseModel):
    """Preferences to change; a field left out stays as it is."""

    name: str | None = None
    user_memory_enabled: bool | None = None
    photo_viewing_enabled: bool | None = None
    country: str | None = None
    time_zone: str | None = None


class CheckInSettingsRequest(BaseModel):
    """Check-in settings to change; a field left out stays as it is."""

    enabled: bool | None = None
    frequency: CheckInFrequency | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class PauseRequest(BaseModel):
    """How long to pause Check-ins for."""

    length: PauseLength


class RecentCheckInResponse(BaseModel):
    """A Check-in sent or skipped and whether the User replied; never a reason.

    `skipped_for_daily_limit` says whether it was skipped because the User had
    used up the day's daily message limit.
    """

    id: str
    outcome: CheckInOutcome
    kind: str | None
    decided_at: datetime
    status: CheckInStatus
    skipped_for_daily_limit: bool


class CheckInKindSummaryResponse(BaseModel):
    """A Check-in Kind as Users see it, read-only."""

    name: str
    description: str


class CheckInsResponse(BaseModel):
    """A User's Check-in settings and recent Check-ins; never a next time."""

    enabled: bool
    available: bool
    frequency: CheckInFrequency
    quiet_hours_start: time
    quiet_hours_end: time
    paused: bool
    paused_until: datetime | None
    recent: list[RecentCheckInResponse]
    kinds: list[CheckInKindSummaryResponse]


class PlatformContentResponse(BaseModel):
    """Admin-managed wording and settings the Dashboard shows to Users."""

    ai_notice: str
    ai_notice_short: str
    user_memory_explanation: str
    photo_viewing_explanation: str
    onboarding_reason_choices: list[str]
    message_retention_days: int


class ConnectionTokenResponse(BaseModel):
    """A connection token and how to use it."""

    token: str
    deep_link_url: str
    bot_username: str
    expires_at: datetime
    status: ConnectionTokenStatus


class TelegramConnectionResponse(BaseModel):
    """A made Telegram Connection."""

    telegram_username: str | None
    connected_at: datetime


class TelegramConnectionStatusResponse(BaseModel):
    """A User's Telegram Connection and their newest connection token."""

    connection: TelegramConnectionResponse | None
    latest_token: ConnectionTokenResponse | None


class MemoryItemResponse(BaseModel):
    """A Memory Item and where it came from."""

    id: str
    content: str
    source: MemorySource
    created_at: datetime
    updated_at: datetime


class MemoryGroupResponse(BaseModel):
    """A User's Memory Items in one Memory Category."""

    category: str
    items: list[MemoryItemResponse]


class RememberedItemResponse(MemoryItemResponse):
    """A Memory Item with the name of its Memory Category."""

    category: str


class HomeCheckInsResponse(BaseModel):
    """A User's Check-in status and the last Check-in sent; never a next time."""

    enabled: bool
    available: bool
    frequency: CheckInFrequency
    quiet_hours_start: time
    quiet_hours_end: time
    paused: bool
    paused_until: datetime | None
    pause_changed_in_chat_at: datetime | None
    last_sent: RecentCheckInResponse | None


class HomeResponse(BaseModel):
    """What the Dashboard home shows a User."""

    name: str | None
    time_zone: str | None
    telegram_connection: TelegramConnectionResponse | None
    telegram_chat_url: str
    last_conversation_at: datetime | None
    check_ins: HomeCheckInsResponse
    user_memory_enabled: bool
    goals: list[MemoryItemResponse]
    recently_remembered: list[RememberedItemResponse]
    ai_notice: str


class MemoryItemsResponse(BaseModel):
    """A User's Memory Items by Memory Category, in category order."""

    groups: list[MemoryGroupResponse]


class ConversationSummaryResponse(BaseModel):
    """A Conversation Summary and how the User seemed."""

    id: str
    summary: str
    mood: str
    created_at: datetime


class ConversationSummariesResponse(BaseModel):
    """A User's Conversation Summaries, newest first."""

    summaries: list[ConversationSummaryResponse]


class SharedPhotoResponse(BaseModel):
    """A Shared Photo, without the chat channel's IDs."""

    id: str
    description: str
    note: str
    caption: str
    sent_at: datetime


class SharedPhotosResponse(BaseModel):
    """A User's Shared Photos, newest first."""

    photos: list[SharedPhotoResponse]


class PersonalStickerResponse(BaseModel):
    """A Personal Sticker, without the chat channel's IDs."""

    id: str
    emoji: str | None
    note: str
    has_image: bool
    kept_at: datetime


class PersonalStickersResponse(BaseModel):
    """A User's Personal Stickers, most recently used first."""

    stickers: list[PersonalStickerResponse]


def to_memory_item_response(item: MemoryItem) -> MemoryItemResponse:
    """Describe a Memory Item for the Dashboard.

    Args:
        item: The Memory Item.

    Returns:
        The response body.
    """
    return MemoryItemResponse(
        id=str(item.id),
        content=item.content,
        source=item.source,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def to_memory_items_response(groups: list[MemoryGroup]) -> MemoryItemsResponse:
    """Describe a User's Memory Items for the Dashboard.

    Args:
        groups: The Memory Items by Memory Category.

    Returns:
        The response body.
    """
    return MemoryItemsResponse(
        groups=[
            MemoryGroupResponse(
                category=group.category.name,
                items=[to_memory_item_response(item) for item in group.items],
            )
            for group in groups
        ]
    )


def to_summary_response(summary: ConversationSummary) -> ConversationSummaryResponse:
    """Describe a Conversation Summary for the Dashboard.

    Args:
        summary: The Conversation Summary.

    Returns:
        The response body.
    """
    return ConversationSummaryResponse(
        id=str(summary.id),
        summary=summary.summary,
        mood=summary.mood,
        created_at=summary.created_at,
    )


def to_shared_photo_response(photo: SharedPhoto) -> SharedPhotoResponse:
    """Describe a Shared Photo for the Dashboard; never its chat channel IDs.

    Args:
        photo: The Shared Photo.

    Returns:
        The response body.
    """
    return SharedPhotoResponse(
        id=str(photo.id),
        description=photo.description,
        note=photo.note,
        caption=photo.caption,
        sent_at=photo.sent_at,
    )


def to_personal_sticker_response(sticker: PersonalSticker) -> PersonalStickerResponse:
    """Describe a Personal Sticker for the Dashboard; never its chat channel IDs.

    Args:
        sticker: The Personal Sticker.

    Returns:
        The response body.
    """
    return PersonalStickerResponse(
        id=str(sticker.id),
        emoji=sticker.emoji,
        note=sticker.note,
        has_image=sticker.preview_file_id is not None,
        kept_at=sticker.kept_at,
    )


def to_recent_check_in_response(recent: RecentCheckIn) -> RecentCheckInResponse:
    """Describe a Check-in for the Dashboard; never its message or skip reason.

    Args:
        recent: The Check-in and what happened after it.

    Returns:
        The response body.
    """
    return RecentCheckInResponse(
        id=str(recent.check_in.id),
        outcome=recent.check_in.outcome,
        kind=recent.check_in.kind_name,
        decided_at=recent.check_in.decided_at,
        status=recent.status,
        skipped_for_daily_limit=recent.check_in.skipped_for_daily_limit,
    )


def to_me_response(
    user: User,
    user_memory_available: bool,
    photo_viewing_available: bool,
    personal_stickers_available: bool,
) -> MeResponse:
    """Describe a User for the Dashboard.

    Args:
        user: The User.
        user_memory_available: Whether the Admin side allows User Memory
            for them.
        photo_viewing_available: Whether the Admin side allows Photo Viewing
            for them.
        personal_stickers_available: Whether Personal Stickers works for
            them; they have no switch of their own.

    Returns:
        The response body.
    """
    return MeResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        onboarding_reasons=list(user.onboarding_reasons),
        onboarding_note=user.onboarding_note,
        country=user.country,
        time_zone=user.time_zone,
        ai_notice_acknowledged_at=user.ai_notice_acknowledged_at,
        user_memory_enabled=user.user_memory_enabled,
        user_memory_available=user_memory_available,
        photo_viewing_enabled=user.photo_viewing_enabled,
        photo_viewing_available=photo_viewing_available,
        personal_stickers_available=personal_stickers_available,
        onboarding_completed_at=user.onboarding_completed_at,
        role=user.role,
        changed_in_chat=user.settings_changed_in_chat,
    )


def build_dashboard_api_router(
    current_user: Callable[..., User],
    user_service: UserService,
    user_memory_service: UserMemoryService,
    check_in_service: CheckInService,
    telegram_connection_service: TelegramConnectionService,
    user_data_service: UserDataService,
    home_service: HomeService,
    feature_service: FeatureService,
    photo_service: PhotoService,
    personal_sticker_service: PersonalStickerService,
    platform_settings: PlatformSettingsRepository,
    telegram_bot_username: str,
) -> APIRouter:
    """Build the Dashboard API routes.

    Every route needs a valid bearer token; the User is created on their
    first request.

    Args:
        current_user: The dependency that finds the User making a request.
        user_service: Keeps the User's profile.
        user_memory_service: Shows and deletes the User's User Memory.
        check_in_service: Keeps the User's Check-in settings.
        telegram_connection_service: Issues tokens and reports connection status.
        user_data_service: Deletes the User's data or account.
        home_service: Gathers what the Dashboard home shows.
        feature_service: Says whether the Admin side allows User Memory,
            Check-ins and Photo Viewing for the User, and whether Personal
            Stickers works for them.
        photo_service: Lists, downloads and deletes the User's Shared Photos.
        personal_sticker_service: Lists, downloads and removes the User's
            Personal Stickers.
        platform_settings: Admin-managed wording shown on the Dashboard.
        telegram_bot_username: The Companion's Telegram @username, for deep links.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api")
    telegram_chat_url = f"https://t.me/{telegram_bot_username}"

    def me_response(user: User) -> MeResponse:
        """Describe a User, with which of their Features are available.

        Args:
            user: The User.

        Returns:
            The response body.
        """
        return to_me_response(
            user,
            feature_service.available_for(user.id, Feature.USER_MEMORY),
            feature_service.available_for(user.id, Feature.PHOTO_VIEWING),
            feature_service.works_for(user.id, Feature.PERSONAL_STICKERS),
        )

    def to_check_ins_response(user: User) -> CheckInsResponse:
        """Describe a User's Check-in settings and recent Check-ins.

        Args:
            user: The User.

        Returns:
            The response body, with the pause as it stands right now and the
            Check-in Kinds that may be sent to them.
        """
        settings = user.check_ins
        is_paused = check_in_service.is_paused(user)
        return CheckInsResponse(
            enabled=settings.enabled,
            available=feature_service.available_for(user.id, Feature.CHECK_INS),
            frequency=settings.frequency,
            quiet_hours_start=settings.quiet_hours_start,
            quiet_hours_end=settings.quiet_hours_end,
            paused=is_paused,
            paused_until=settings.paused_until if is_paused else None,
            recent=[
                to_recent_check_in_response(recent)
                for recent in check_in_service.list_recent(user)
            ],
            kinds=[
                CheckInKindSummaryResponse(name=kind.name, description=kind.description)
                for kind in check_in_service.kinds_for(user)
            ],
        )

    def to_token_response(
        token: ConnectionToken, token_status: ConnectionTokenStatus
    ) -> ConnectionTokenResponse:
        """Describe a connection token for the Dashboard.

        Args:
            token: The token.
            token_status: Its status right now.

        Returns:
            The response body.
        """
        return ConnectionTokenResponse(
            token=token.token,
            deep_link_url=f"{telegram_chat_url}?start={token.token}",
            bot_username=telegram_bot_username,
            expires_at=token.expires_at,
            status=token_status,
        )

    def to_home_response(user: User, home: Home) -> HomeResponse:
        """Describe a User's Dashboard home.

        Args:
            user: The User.
            home: What their home shows.

        Returns:
            The response body, with the pause as it stands right now.
        """
        settings = user.check_ins
        connection = home.telegram_connection
        return HomeResponse(
            name=user.name,
            time_zone=user.time_zone,
            telegram_connection=(
                TelegramConnectionResponse(
                    telegram_username=connection.telegram_username,
                    connected_at=connection.connected_at,
                )
                if connection
                else None
            ),
            telegram_chat_url=telegram_chat_url,
            last_conversation_at=home.last_conversation_at,
            check_ins=HomeCheckInsResponse(
                enabled=settings.enabled,
                available=feature_service.available_for(user.id, Feature.CHECK_INS),
                frequency=settings.frequency,
                quiet_hours_start=settings.quiet_hours_start,
                quiet_hours_end=settings.quiet_hours_end,
                paused=home.check_ins_paused,
                paused_until=settings.paused_until if home.check_ins_paused else None,
                pause_changed_in_chat_at=user.settings_changed_in_chat.get(
                    ChatSetting.CHECK_IN_PAUSE
                ),
                last_sent=(
                    to_recent_check_in_response(home.last_check_in)
                    if home.last_check_in
                    else None
                ),
            ),
            user_memory_enabled=user.user_memory_enabled,
            goals=[to_memory_item_response(item) for item in home.goals],
            recently_remembered=[
                RememberedItemResponse(
                    **to_memory_item_response(remembered.item).model_dump(),
                    category=remembered.category,
                )
                for remembered in home.recently_remembered
            ],
            ai_notice=platform_settings.get("ai_notice_short"),
        )

    @router.get("/me")
    def get_me(user: Annotated[User, Depends(current_user)]) -> MeResponse:
        """Return the signed-in User, creating them on first visit.

        Args:
            user: The signed-in User.

        Returns:
            The User.
        """
        return me_response(user)

    @router.patch("/me")
    def update_me(
        user: Annotated[User, Depends(current_user)], request: PreferencesRequest
    ) -> MeResponse:
        """Change the User's name, own Feature switches, country or time zone.

        Args:
            user: The signed-in User.
            request: The preferences to change.

        Returns:
            The updated User.

        Raises:
            HTTPException: 422 if a new value is not acceptable; 403 if it
                changes User Memory or Photo Viewing while the Admin side has
                it off.
        """
        changes = PreferenceChanges(
            name=request.name,
            user_memory_enabled=request.user_memory_enabled,
            photo_viewing_enabled=request.photo_viewing_enabled,
            country=request.country,
            time_zone=request.time_zone,
        )
        try:
            return me_response(user_service.update_preferences(user, changes))
        except InvalidProfileError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        except FeatureNotAvailableError as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_AVAILABLE) from error

    @router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
    def delete_account(user: Annotated[User, Depends(current_user)]) -> Response:
        """Delete the User's account and everything of theirs.

        Args:
            user: The signed-in User.

        Returns:
            An empty response.

        Raises:
            HTTPException: 409 if they are the only Admin.
        """
        try:
            user_data_service.delete_account(user)
        except LastAdminError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "You’re the only Admin. Make someone else an Admin before "
                "deleting your account.",
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.delete("/me/data", status_code=status.HTTP_204_NO_CONTENT)
    def delete_my_data(user: Annotated[User, Depends(current_user)]) -> Response:
        """Delete the User's messages, memory, Check-ins and Telegram Connection.

        Args:
            user: The signed-in User.

        Returns:
            An empty response.
        """
        user_data_service.delete_data(user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.put("/onboarding")
    def complete_onboarding(
        user: Annotated[User, Depends(current_user)], request: OnboardingRequest
    ) -> MeResponse:
        """Save the User's onboarding answers and mark onboarding done.

        Args:
            user: The signed-in User.
            request: Their answers.

        Returns:
            The updated User.

        Raises:
            HTTPException: 422 if the AI notice was not acknowledged or an
                answer is not acceptable.
        """
        answers = OnboardingAnswers(
            name=request.name,
            ai_notice_acknowledged=request.ai_notice_acknowledged,
            onboarding_reasons=tuple(request.onboarding_reasons),
            onboarding_note=request.onboarding_note,
            user_memory_enabled=request.user_memory_enabled,
            country=request.country,
            time_zone=request.time_zone,
            check_ins=CheckInChanges(
                enabled=request.check_ins_enabled,
                frequency=request.check_in_frequency,
                quiet_hours_start=request.quiet_hours_start,
                quiet_hours_end=request.quiet_hours_end,
            ),
        )
        try:
            return me_response(user_service.complete_onboarding(user, answers))
        except InvalidProfileError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error

    @router.get("/home")
    def get_home(user: Annotated[User, Depends(current_user)]) -> HomeResponse:
        """Return what the Dashboard home shows the User.

        Args:
            user: The signed-in User.

        Returns:
            Their Telegram Connection, Check-in status, Goals, newest Memory
            Items and the AI notice.
        """
        return to_home_response(user, home_service.get(user))

    @router.get("/check-ins")
    def get_check_ins(user: Annotated[User, Depends(current_user)]) -> CheckInsResponse:
        """Return the User's Check-in settings and recent Check-ins.

        Args:
            user: The signed-in User.

        Returns:
            The settings and recent Check-ins.
        """
        return to_check_ins_response(user)

    @router.patch("/check-ins")
    def update_check_ins(
        user: Annotated[User, Depends(current_user)], request: CheckInSettingsRequest
    ) -> CheckInsResponse:
        """Change the User's Check-in frequency or quiet hours, or turn them off.

        Args:
            user: The signed-in User.
            request: The settings to change.

        Returns:
            The updated settings and recent Check-ins.

        Raises:
            HTTPException: 403 if it turns Check-ins on or off while the Admin
                side has them off.
        """
        changes = CheckInChanges(
            enabled=request.enabled,
            frequency=request.frequency,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
        )
        try:
            saved = check_in_service.change_settings(user, changes)
        except FeatureNotAvailableError as error:
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_AVAILABLE) from error
        return to_check_ins_response(saved)

    @router.put("/check-ins/pause")
    def pause_check_ins(
        user: Annotated[User, Depends(current_user)], request: PauseRequest
    ) -> CheckInsResponse:
        """Pause the User's Check-ins for a day, a week or until they resume.

        Args:
            user: The signed-in User.
            request: How long to pause for.

        Returns:
            The updated settings and recent Check-ins.
        """
        return to_check_ins_response(check_in_service.pause(user, request.length))

    @router.delete("/check-ins/pause")
    def resume_check_ins(
        user: Annotated[User, Depends(current_user)],
    ) -> CheckInsResponse:
        """End the pause on the User's Check-ins.

        Args:
            user: The signed-in User.

        Returns:
            The updated settings and recent Check-ins.
        """
        return to_check_ins_response(check_in_service.resume(user))

    @router.get("/platform-content")
    def get_platform_content(
        user: Annotated[User, Depends(current_user)],
    ) -> PlatformContentResponse:
        """Return the Admin-managed wording the Dashboard shows to Users.

        Args:
            user: The signed-in User.

        Returns:
            The AI notice, User Memory explanation, onboarding choices and how
            long messages are kept.
        """
        return PlatformContentResponse(
            ai_notice=platform_settings.get("ai_notice"),
            ai_notice_short=platform_settings.get("ai_notice_short"),
            user_memory_explanation=platform_settings.get("user_memory_explanation"),
            photo_viewing_explanation=platform_settings.get(
                "photo_viewing_explanation"
            ),
            onboarding_reason_choices=platform_settings.get(
                "onboarding_reason_choices"
            ),
            message_retention_days=platform_settings.get(RETENTION_DAYS_SETTING),
        )

    @router.get("/telegram-connection")
    def get_telegram_connection(
        user: Annotated[User, Depends(current_user)],
    ) -> TelegramConnectionStatusResponse:
        """Return the User's Telegram Connection and newest connection token.

        Args:
            user: The signed-in User.

        Returns:
            The connection status.
        """
        connection_status = telegram_connection_service.get_status(user.id)
        connection = connection_status.connection
        latest_token = connection_status.latest_token
        latest_token_status = connection_status.latest_token_status
        return TelegramConnectionStatusResponse(
            connection=(
                TelegramConnectionResponse(
                    telegram_username=connection.telegram_username,
                    connected_at=connection.connected_at,
                )
                if connection
                else None
            ),
            latest_token=(
                to_token_response(latest_token, latest_token_status)
                if latest_token and latest_token_status
                else None
            ),
        )

    @router.post("/telegram-connection/tokens", status_code=status.HTTP_201_CREATED)
    def create_connection_token(
        user: Annotated[User, Depends(current_user)],
    ) -> ConnectionTokenResponse:
        """Issue a new one-time connection token.

        Args:
            user: The signed-in User.

        Returns:
            The new token and its Telegram deep link.

        Raises:
            HTTPException: 409 if the User hasn't finished onboarding.
        """
        try:
            token = telegram_connection_service.create_token(user)
        except OnboardingNotFinishedError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
        return to_token_response(token, ConnectionTokenStatus.ACTIVE)

    @router.get("/memory-items")
    def list_memory_items(
        user: Annotated[User, Depends(current_user)],
    ) -> MemoryItemsResponse:
        """Return the User's Memory Items by Memory Category.

        Args:
            user: The signed-in User.

        Returns:
            The Memory Items.
        """
        return to_memory_items_response(user_memory_service.list_groups(user.id))

    @router.delete("/memory-items", status_code=status.HTTP_204_NO_CONTENT)
    def delete_all_memory_items(
        user: Annotated[User, Depends(current_user)],
    ) -> Response:
        """Delete every one of the User's Memory Items; Summaries stay.

        Args:
            user: The signed-in User.

        Returns:
            An empty response.
        """
        user_memory_service.delete_all_items(user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.delete("/memory-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_memory_item(
        user: Annotated[User, Depends(current_user)], item_id: UUID
    ) -> Response:
        """Delete one of the User's Memory Items.

        Args:
            user: The signed-in User.
            item_id: The Memory Item's ID.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if the User has no such Memory Item.
        """
        try:
            user_memory_service.delete_item(user.id, item_id)
        except MemoryNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Memory not found"
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/conversation-summaries")
    def list_conversation_summaries(
        user: Annotated[User, Depends(current_user)],
    ) -> ConversationSummariesResponse:
        """Return the User's Conversation Summaries, newest first.

        Args:
            user: The signed-in User.

        Returns:
            The Conversation Summaries.
        """
        return ConversationSummariesResponse(
            summaries=[
                to_summary_response(summary)
                for summary in user_memory_service.list_summaries(user.id)
            ]
        )

    @router.delete(
        "/conversation-summaries/{summary_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_conversation_summary(
        user: Annotated[User, Depends(current_user)], summary_id: UUID
    ) -> Response:
        """Delete one of the User's Conversation Summaries.

        Args:
            user: The signed-in User.
            summary_id: The Conversation Summary's ID.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if the User has no such Conversation Summary.
        """
        try:
            user_memory_service.delete_summary(user.id, summary_id)
        except MemoryNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Conversation Summary not found"
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/shared-photos")
    def list_shared_photos(
        user: Annotated[User, Depends(current_user)],
    ) -> SharedPhotosResponse:
        """Return the User's Shared Photos, newest first.

        Args:
            user: The signed-in User.

        Returns:
            The Shared Photos.
        """
        return SharedPhotosResponse(
            photos=[
                to_shared_photo_response(photo)
                for photo in photo_service.list_shared(user.id)
            ]
        )

    @router.get("/shared-photos/{photo_id}/image")
    def get_shared_photo_image(
        user: Annotated[User, Depends(current_user)], photo_id: UUID
    ) -> Response:
        """Return the image of one of the User's Shared Photos.

        It is downloaded from the chat channel, so the bot token stays private.

        Args:
            user: The signed-in User.
            photo_id: The Shared Photo's ID.

        Returns:
            The image.

        Raises:
            HTTPException: 404 if the User has no such Shared Photo or it
                couldn't be downloaded.
        """
        try:
            image = photo_service.shared_photo_image(user.id, photo_id)
        except SharedPhotoNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Shared Photo not found"
            ) from error
        if image is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "This photo couldn't be downloaded"
            )
        return Response(
            content=image.content,
            media_type=image.media_type,
            headers={"Cache-Control": "private, max-age=86400"},
        )

    @router.delete("/shared-photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_shared_photo(
        user: Annotated[User, Depends(current_user)], photo_id: UUID
    ) -> Response:
        """Delete one of the User's Shared Photos.

        Args:
            user: The signed-in User.
            photo_id: The Shared Photo's ID.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if the User has no such Shared Photo.
        """
        try:
            photo_service.delete_shared(user.id, photo_id)
        except SharedPhotoNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Shared Photo not found"
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/personal-stickers")
    def list_personal_stickers(
        user: Annotated[User, Depends(current_user)],
    ) -> PersonalStickersResponse:
        """Return the User's Personal Stickers, most recently used first.

        Args:
            user: The signed-in User.

        Returns:
            The Personal Stickers.
        """
        return PersonalStickersResponse(
            stickers=[
                to_personal_sticker_response(sticker)
                for sticker in personal_sticker_service.list_for(user.id)
            ]
        )

    @router.get("/personal-stickers/{sticker_id}/image")
    def get_personal_sticker_image(
        user: Annotated[User, Depends(current_user)], sticker_id: UUID
    ) -> Response:
        """Return the image of one of the User's Personal Stickers.

        It is downloaded from the chat channel, so the bot token stays private.

        Args:
            user: The signed-in User.
            sticker_id: The Personal Sticker's ID.

        Returns:
            The image.

        Raises:
            HTTPException: 404 if the User has no such sticker, or it has no
                image or it couldn't be downloaded.
        """
        try:
            image = personal_sticker_service.get_image(user.id, sticker_id)
        except PersonalStickerNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Personal Sticker not found"
            ) from error
        if image is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "This sticker has no image to show"
            )
        return Response(
            content=image.content,
            media_type=image.media_type,
            headers={"Cache-Control": "private, max-age=86400"},
        )

    @router.delete(
        "/personal-stickers/{sticker_id}", status_code=status.HTTP_204_NO_CONTENT
    )
    def delete_personal_sticker(
        user: Annotated[User, Depends(current_user)], sticker_id: UUID
    ) -> Response:
        """Remove one of the User's Personal Stickers.

        Args:
            user: The signed-in User.
            sticker_id: The Personal Sticker's ID.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if the User has no such sticker.
        """
        try:
            personal_sticker_service.remove(user.id, sticker_id)
        except PersonalStickerNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Personal Sticker not found"
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
