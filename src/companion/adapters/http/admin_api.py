from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from companion.core.admin_users import (
    AdminUserService,
    LastAdminError,
    UserNotFoundError,
)
from companion.core.models import StoredSetting, User, UserOverview, UserRole
from companion.core.platform_settings import (
    CORE_SERVICES,
    InvalidSettingError,
    PlatformSettingsService,
)


class AdminUserResponse(BaseModel):
    """A User as Admins see them: activity counts, never message text."""

    id: str
    name: str | None
    email: str | None
    role: UserRole
    signed_up_at: datetime
    telegram_connected: bool
    conversation_count: int
    messages_sent: int


class RoleRequest(BaseModel):
    """The role to give a User."""

    role: UserRole


class RoleResponse(BaseModel):
    """A User's role after a change."""

    id: str
    role: UserRole


class AdminUserListResponse(BaseModel):
    """Every User, newest sign-up first."""

    users: list[AdminUserResponse]


class SettingResponse(BaseModel):
    """A platform setting's value and when it was last saved."""

    value: Any
    updated_at: datetime
    updated_by: str | None


class SettingsResponse(BaseModel):
    """Every setting Admins may change, by key."""

    settings: dict[str, SettingResponse]


class SettingsUpdateRequest(BaseModel):
    """New values for some settings, by key; others stay as they are."""

    values: dict[str, Any]


class CoreServiceResponse(BaseModel):
    """A core service whose prompt and model Admins can change."""

    name: str
    runs_when: str
    description: str
    prompt_key: str
    model_key: str


class CoreServicesResponse(BaseModel):
    """The core services and the models Admins can pick for them."""

    services: list[CoreServiceResponse]
    model_choices: list[str]


def to_settings_response(settings: list[StoredSetting]) -> SettingsResponse:
    """Describe settings for the admin area.

    Args:
        settings: The settings.

    Returns:
        The response body.
    """
    return SettingsResponse(
        settings={
            setting.key: SettingResponse(
                value=setting.value,
                updated_at=setting.updated_at,
                updated_by=setting.updated_by_name,
            )
            for setting in settings
        }
    )


def to_admin_user_response(overview: UserOverview) -> AdminUserResponse:
    """Describe a User for the admin area.

    Args:
        overview: The User and their activity counts.

    Returns:
        The response body.
    """
    return AdminUserResponse(
        id=str(overview.user.id),
        name=overview.user.name,
        email=overview.user.email,
        role=overview.user.role,
        signed_up_at=overview.user.created_at,
        telegram_connected=overview.telegram_connected,
        conversation_count=overview.conversation_count,
        messages_sent=overview.messages_sent,
    )


def build_admin_api_router(
    current_admin: Callable[..., User],
    admin_user_service: AdminUserService,
    platform_settings_service: PlatformSettingsService,
) -> APIRouter:
    """Build the admin API routes.

    The Admin check sits on the router itself, so every route added here
    refuses anyone who is not an Admin.

    Args:
        current_admin: The dependency that lets only Admins through.
        admin_user_service: Lists Users and changes roles.
        platform_settings_service: Reads and changes platform settings.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    @router.get("/users")
    def list_users() -> AdminUserListResponse:
        """List every User with activity counts.

        Returns:
            The Users, newest sign-up first.
        """
        return AdminUserListResponse(
            users=[
                to_admin_user_response(overview)
                for overview in admin_user_service.list_users()
            ]
        )

    @router.put("/users/{user_id}/role")
    def change_role(user_id: UUID, request: RoleRequest) -> RoleResponse:
        """Promote a User to Admin or demote an Admin.

        Args:
            user_id: The User to change.
            request: Their new role.

        Returns:
            The User's role after the change.

        Raises:
            HTTPException: 404 if there is no such User; 409 if they are the
                last Admin and would be demoted.
        """
        try:
            user = admin_user_service.change_role(user_id, request.role)
        except UserNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No such User") from error
        except LastAdminError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This is the last Admin. Make someone else an Admin first.",
            ) from error
        return RoleResponse(id=str(user.id), role=user.role)

    @router.get("/settings")
    def get_settings() -> SettingsResponse:
        """Return every setting Admins may change.

        Returns:
            The settings, by key.
        """
        return to_settings_response(platform_settings_service.list_editable())

    @router.patch("/settings")
    def update_settings(
        admin: Annotated[User, Depends(current_admin)],
        request: SettingsUpdateRequest,
    ) -> SettingsResponse:
        """Save new values for some settings, all together or not at all.

        Args:
            admin: The Admin making the change.
            request: The new values.

        Returns:
            Every editable setting after the change.

        Raises:
            HTTPException: 422 if a key may not be changed or a value is not
                valid.
        """
        try:
            saved = platform_settings_service.update(admin, request.values)
        except InvalidSettingError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_settings_response(saved)

    @router.get("/core-services")
    def list_core_services() -> CoreServicesResponse:
        """Return the core services and the models Admins can pick.

        Returns:
            The services, each naming its prompt and model settings.
        """
        return CoreServicesResponse(
            services=[
                CoreServiceResponse(
                    name=service.name,
                    runs_when=service.runs_when,
                    description=service.description,
                    prompt_key=service.prompt_key,
                    model_key=service.model_key,
                )
                for service in CORE_SERVICES
            ],
            model_choices=platform_settings_service.model_choices(),
        )

    return router
