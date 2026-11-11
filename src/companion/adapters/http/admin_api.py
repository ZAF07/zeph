from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from companion.core.admin_users import (
    AdminUserService,
    LastAdminError,
    UserNotFoundError,
)
from companion.core.helplines import (
    FallbackHelplineError,
    HelplineNotFoundError,
    HelplineService,
    InvalidHelplineError,
    MoveDirection,
)
from companion.core.models import (
    Helpline,
    HelplineDetails,
    RiskType,
    SafeguardEventOverview,
    StoredSetting,
    User,
    UserOverview,
    UserRole,
)
from companion.core.platform_settings import (
    CORE_SERVICES,
    InvalidSettingError,
    PlatformSettingsService,
)
from companion.core.safeguard import InvalidEventFilterError, Safeguard


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


class HelplineResponse(BaseModel):
    """A Helpline; the international fallback has no country."""

    id: str
    country: str | None
    name: str
    number: str
    hours: str | None
    sort_order: int


class HelplinesResponse(BaseModel):
    """Every country's Helplines, by country and order, and the fallback."""

    helplines: list[HelplineResponse]
    international_fallback: HelplineResponse


class CountryHelplinesResponse(BaseModel):
    """One country's Helplines in order."""

    helplines: list[HelplineResponse]


class HelplineDetailsRequest(BaseModel):
    """A Helpline's name, number and hours."""

    name: str
    number: str
    hours: str | None = None

    def to_details(self) -> HelplineDetails:
        """Turn the request into Helpline details.

        Returns:
            The details.
        """
        return HelplineDetails(name=self.name, number=self.number, hours=self.hours)


class HelplineRequest(HelplineDetailsRequest):
    """A country Helpline as an Admin enters it."""

    country: str


class MoveRequest(BaseModel):
    """Which way to move a Helpline in its country's list."""

    direction: MoveDirection


class SafeguardEventResponse(BaseModel):
    """A Safeguard Event: who, when and what kind of risk. Never message text."""

    id: str
    user_id: str
    user_name: str | None
    user_email: str | None
    risk_type: RiskType
    created_at: datetime
    helplines_country: str | None


class SafeguardEventsResponse(BaseModel):
    """Safeguard Events, newest first."""

    events: list[SafeguardEventResponse]


def to_helpline_response(helpline: Helpline) -> HelplineResponse:
    """Describe a Helpline for the admin area.

    Args:
        helpline: The Helpline.

    Returns:
        The response body.
    """
    return HelplineResponse(
        id=str(helpline.id),
        country=helpline.country,
        name=helpline.details.name,
        number=helpline.details.number,
        hours=helpline.details.hours,
        sort_order=helpline.sort_order,
    )


def to_safeguard_event_response(
    overview: SafeguardEventOverview,
) -> SafeguardEventResponse:
    """Describe a Safeguard Event for the admin area.

    Args:
        overview: The event and who the User is.

    Returns:
        The response body.
    """
    return SafeguardEventResponse(
        id=str(overview.event.id),
        user_id=str(overview.event.user_id),
        user_name=overview.user_name,
        user_email=overview.user_email,
        risk_type=overview.event.risk_type,
        created_at=overview.event.created_at,
        helplines_country=overview.event.helplines_country,
    )


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
    helpline_service: HelplineService,
    safeguard: Safeguard,
) -> APIRouter:
    """Build the admin API routes.

    The Admin check sits on the router itself, so every route added here
    refuses anyone who is not an Admin.

    Args:
        current_admin: The dependency that lets only Admins through.
        admin_user_service: Lists Users and changes roles.
        platform_settings_service: Reads and changes platform settings.
        helpline_service: Manages Helplines and the international fallback.
        safeguard: Lists Safeguard Events.

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

    @router.get("/helplines")
    def list_helplines() -> HelplinesResponse:
        """Return every country's Helplines and the international fallback.

        Returns:
            The Helplines, by country and order, and the fallback.
        """
        return HelplinesResponse(
            helplines=[
                to_helpline_response(helpline)
                for helpline in helpline_service.list_countries()
            ],
            international_fallback=to_helpline_response(
                helpline_service.international_fallback()
            ),
        )

    @router.post("/helplines", status_code=status.HTTP_201_CREATED)
    def add_helpline(request: HelplineRequest) -> HelplineResponse:
        """Add a Helpline last in its country's list.

        Args:
            request: The Helpline.

        Returns:
            The saved Helpline.

        Raises:
            HTTPException: 422 if the country or details are not valid.
        """
        try:
            helpline = helpline_service.add(request.country, request.to_details())
        except InvalidHelplineError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_helpline_response(helpline)

    @router.put("/helplines/international-fallback")
    def update_international_fallback(
        request: HelplineDetailsRequest,
    ) -> HelplineResponse:
        """Change the international fallback.

        Args:
            request: Its new name, number and hours.

        Returns:
            The saved fallback.

        Raises:
            HTTPException: 422 if the details are not valid.
        """
        try:
            fallback = helpline_service.update_international_fallback(
                request.to_details()
            )
        except InvalidHelplineError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_helpline_response(fallback)

    @router.put("/helplines/{helpline_id}")
    def update_helpline(
        helpline_id: UUID, request: HelplineRequest
    ) -> HelplineResponse:
        """Change a country Helpline.

        Args:
            helpline_id: The Helpline to change.
            request: Its new country, name, number and hours.

        Returns:
            The saved Helpline.

        Raises:
            HTTPException: 404 if there is no such Helpline; 422 if the country
                or details are not valid.
        """
        try:
            helpline = helpline_service.update(
                helpline_id, request.country, request.to_details()
            )
        except HelplineNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Helpline"
            ) from error
        except InvalidHelplineError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_helpline_response(helpline)

    @router.delete("/helplines/{helpline_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_helpline(helpline_id: UUID) -> Response:
        """Remove a country Helpline.

        Args:
            helpline_id: The Helpline to remove.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if there is no such Helpline; 409 if it is the
                international fallback.
        """
        try:
            helpline_service.delete(helpline_id)
        except HelplineNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Helpline"
            ) from error
        except FallbackHelplineError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "The international fallback can't be removed, only edited.",
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post("/helplines/{helpline_id}/move")
    def move_helpline(
        helpline_id: UUID, request: MoveRequest
    ) -> CountryHelplinesResponse:
        """Move a Helpline up or down in its country's list.

        Args:
            helpline_id: The Helpline to move.
            request: Which way to move it.

        Returns:
            Its country's Helplines in their new order.

        Raises:
            HTTPException: 404 if there is no such country Helpline.
        """
        try:
            helplines = helpline_service.move(helpline_id, request.direction)
        except HelplineNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Helpline"
            ) from error
        return CountryHelplinesResponse(
            helplines=[to_helpline_response(helpline) for helpline in helplines]
        )

    @router.get("/safeguard-events")
    def list_safeguard_events(
        risk_type: RiskType | None = None,
        days: Annotated[int | None, Query(ge=1)] = None,
    ) -> SafeguardEventsResponse:
        """List Safeguard Events, newest first. Never includes message text.

        Args:
            risk_type: Only events of this crisis type; every type if left out.
            days: Only events from the last this many days; all time if left
                out.

        Returns:
            The events with who each User is.

        Raises:
            HTTPException: 422 if `risk_type` is "none".
        """
        try:
            overviews = safeguard.list_events(days, risk_type)
        except InvalidEventFilterError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return SafeguardEventsResponse(
            events=[to_safeguard_event_response(overview) for overview in overviews]
        )

    return router
