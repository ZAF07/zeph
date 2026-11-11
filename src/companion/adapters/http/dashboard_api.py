from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from companion.core.models import ConnectionToken, ConnectionTokenStatus, User
from companion.core.ports import AuthVerifier
from companion.core.telegram_connection import TelegramConnectionService
from companion.core.users import UserService


class MeResponse(BaseModel):
    """The signed-in User."""

    id: str
    email: str | None


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


def build_dashboard_api_router(
    auth_verifier: AuthVerifier,
    user_service: UserService,
    telegram_connection_service: TelegramConnectionService,
    telegram_bot_username: str,
) -> APIRouter:
    """Build the Dashboard API routes.

    Every route needs a valid bearer token; the User is created on their
    first request.

    Args:
        auth_verifier: Checks bearer tokens.
        user_service: Finds or creates the User behind a token.
        telegram_connection_service: Issues tokens and reports connection status.
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
        return MeResponse(id=str(user.id), email=user.email)

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
