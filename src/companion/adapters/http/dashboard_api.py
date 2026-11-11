from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from companion.core.models import (
    ConnectionToken,
    ConnectionTokenStatus,
    OnboardingAnswers,
    PreferenceChanges,
    User,
)
from companion.core.ports import AuthVerifier, PlatformSettingsRepository
from companion.core.telegram_connection import TelegramConnectionService
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
    onboarding_completed_at: datetime | None


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


class PreferencesRequest(BaseModel):
    """Preferences to change; a field left out stays as it is."""

    name: str | None = None
    user_memory_enabled: bool | None = None
    country: str | None = None
    time_zone: str | None = None


class PlatformContentResponse(BaseModel):
    """Admin-managed wording the Dashboard shows to Users."""

    ai_notice: str
    ai_notice_short: str
    user_memory_explanation: str
    onboarding_reason_choices: list[str]


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


def to_me_response(user: User) -> MeResponse:
    """Describe a User for the Dashboard.

    Args:
        user: The User.

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
        onboarding_completed_at=user.onboarding_completed_at,
    )


def build_dashboard_api_router(
    auth_verifier: AuthVerifier,
    user_service: UserService,
    telegram_connection_service: TelegramConnectionService,
    platform_settings: PlatformSettingsRepository,
    telegram_bot_username: str,
) -> APIRouter:
    """Build the Dashboard API routes.

    Every route needs a valid bearer token; the User is created on their
    first request.

    Args:
        auth_verifier: Checks bearer tokens.
        user_service: Finds or creates the User behind a token, and keeps their
            profile.
        telegram_connection_service: Issues tokens and reports connection status.
        platform_settings: Admin-managed wording shown on the Dashboard.
        telegram_bot_username: The Companion's Telegram @username, for deep links.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api")

    def current_user(authorization: Annotated[str | None, Header()] = None) -> User:
        """Find the User making the request.

        Args:
            authorization: The `Authorization: Bearer <token>` header.

        Returns:
            The User.

        Raises:
            HTTPException: 401 if the token is missing or not valid.
        """
        scheme, _, token = (authorization or "").partition(" ")
        identity = auth_verifier.verify(token) if scheme == "Bearer" else None
        if identity is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
        return user_service.get_or_create(identity)

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
            deep_link_url=f"https://t.me/{telegram_bot_username}?start={token.token}",
            bot_username=telegram_bot_username,
            expires_at=token.expires_at,
            status=token_status,
        )

    @router.get("/me")
    def get_me(user: Annotated[User, Depends(current_user)]) -> MeResponse:
        """Return the signed-in User, creating them on first visit.

        Args:
            user: The signed-in User.

        Returns:
            The User.
        """
        return to_me_response(user)

    @router.patch("/me")
    def update_me(
        user: Annotated[User, Depends(current_user)], request: PreferencesRequest
    ) -> MeResponse:
        """Change the User's name, User Memory setting, country or time zone.

        Args:
            user: The signed-in User.
            request: The preferences to change.

        Returns:
            The updated User.

        Raises:
            HTTPException: 422 if a new value is not acceptable.
        """
        changes = PreferenceChanges(
            name=request.name,
            user_memory_enabled=request.user_memory_enabled,
            country=request.country,
            time_zone=request.time_zone,
        )
        try:
            return to_me_response(user_service.update_preferences(user, changes))
        except InvalidProfileError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error

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
        )
        try:
            return to_me_response(user_service.complete_onboarding(user, answers))
        except InvalidProfileError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error

    @router.get("/platform-content")
    def get_platform_content(
        user: Annotated[User, Depends(current_user)],
    ) -> PlatformContentResponse:
        """Return the Admin-managed wording the Dashboard shows to Users.

        Args:
            user: The signed-in User.

        Returns:
            The AI notice, User Memory explanation and onboarding choices.
        """
        return PlatformContentResponse(
            ai_notice=platform_settings.get("ai_notice"),
            ai_notice_short=platform_settings.get("ai_notice_short"),
            user_memory_explanation=platform_settings.get("user_memory_explanation"),
            onboarding_reason_choices=platform_settings.get(
                "onboarding_reason_choices"
            ),
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
        """
        token = telegram_connection_service.create_token(user.id)
        return to_token_response(token, ConnectionTokenStatus.ACTIVE)

    return router
