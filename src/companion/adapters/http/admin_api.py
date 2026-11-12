from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
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
from companion.core.knowledge import (
    MAX_UPLOAD_BYTES,
    InvalidKnowledgeDocumentError,
    KnowledgeDocumentNotFoundError,
    KnowledgeFileStillBeingReadError,
    KnowledgeNotRetryableError,
    KnowledgeService,
    knowledge_file_type,
)
from companion.core.memory_categories import (
    InvalidMemoryCategoryError,
    MemoryCategoryNotFoundError,
    MemoryCategoryService,
)
from companion.core.models import (
    Helpline,
    HelplineDetails,
    KnowledgeDetailsChange,
    KnowledgeDocument,
    KnowledgeDocumentWithText,
    KnowledgeFile,
    KnowledgeFileType,
    KnowledgeStatus,
    KnowledgeUpload,
    MemoryCategory,
    MemoryCategoryDetails,
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


class MemoryCategoryResponse(BaseModel):
    """A Memory Category as Admins see it."""

    id: str
    name: str
    description: str
    always_include: bool
    archived: bool


class MemoryCategoryOverviewResponse(MemoryCategoryResponse):
    """A Memory Category and how many Memory Items, across all Users, are in it."""

    item_count: int


class MemoryCategoriesResponse(BaseModel):
    """Every Memory Category in order, archived ones included."""

    categories: list[MemoryCategoryOverviewResponse]


class MemoryCategoryRequest(BaseModel):
    """A Memory Category's name, description and "always include"."""

    name: str
    description: str
    always_include: bool = False

    def to_details(self) -> MemoryCategoryDetails:
        """Turn the request into Memory Category details.

        Returns:
            The details.
        """
        return MemoryCategoryDetails(
            name=self.name,
            description=self.description,
            always_include=self.always_include,
        )


class KnowledgeDocumentResponse(BaseModel):
    """A Knowledge document as Admins see it, without its file."""

    id: str
    title: str
    source: str
    tradition: str
    file_name: str
    file_type: KnowledgeFileType
    status: KnowledgeStatus
    failure_reason: str | None
    text_edited: bool
    created_at: datetime


class KnowledgeDocumentWithTextResponse(KnowledgeDocumentResponse):
    """A Knowledge document with the text replies draw on; null until read."""

    text: str | None


class KnowledgeDetailsRequest(BaseModel):
    """Details to change on a Knowledge document; a field left out is kept."""

    title: str | None = None
    source: str | None = None
    tradition: str | None = None


class KnowledgeTextRequest(BaseModel):
    """The text an Admin wrote for a Knowledge document."""

    text: str


class KnowledgeDocumentsResponse(BaseModel):
    """Every Knowledge document, newest upload first."""

    documents: list[KnowledgeDocumentResponse]


def to_knowledge_document_response(
    document: KnowledgeDocument,
) -> KnowledgeDocumentResponse:
    """Describe a Knowledge document for the admin area.

    Args:
        document: The document.

    Returns:
        The response body.
    """
    return KnowledgeDocumentResponse(
        id=str(document.id),
        title=document.title,
        source=document.source,
        tradition=document.tradition,
        file_name=document.file_name,
        file_type=document.file_type,
        status=document.status,
        failure_reason=document.failure_reason,
        text_edited=document.text_edited,
        created_at=document.created_at,
    )


def to_knowledge_document_with_text_response(
    document_with_text: KnowledgeDocumentWithText,
) -> KnowledgeDocumentWithTextResponse:
    """Describe a Knowledge document and its text for the admin area.

    Args:
        document_with_text: The document and its text.

    Returns:
        The response body.
    """
    return KnowledgeDocumentWithTextResponse(
        **to_knowledge_document_response(document_with_text.document).model_dump(),
        text=document_with_text.text,
    )


def to_knowledge_file(file: UploadFile) -> KnowledgeFile:
    """Read an uploaded Knowledge file, up to one byte over the size limit.

    Args:
        file: The uploaded file.

    Returns:
        The file's name, kind and bytes.

    Raises:
        InvalidKnowledgeDocumentError: If it is not text, Markdown or PDF.
    """
    file_name = file.filename or ""
    return KnowledgeFile(
        file_name=file_name,
        file_type=knowledge_file_type(file_name),
        content=file.file.read(MAX_UPLOAD_BYTES + 1),
    )


def to_memory_category_response(category: MemoryCategory) -> MemoryCategoryResponse:
    """Describe a Memory Category for the admin area.

    Args:
        category: The category.

    Returns:
        The response body.
    """
    return MemoryCategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        always_include=category.always_include,
        archived=category.archived,
    )


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
    memory_category_service: MemoryCategoryService,
    knowledge_service: KnowledgeService,
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
        memory_category_service: Manages Memory Categories.
        knowledge_service: Manages the Knowledge library.

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

    @router.get("/memory-categories")
    def list_memory_categories() -> MemoryCategoriesResponse:
        """List every Memory Category with its Memory Item count.

        Returns:
            The categories in order, archived ones included.
        """
        return MemoryCategoriesResponse(
            categories=[
                MemoryCategoryOverviewResponse(
                    **to_memory_category_response(overview.category).model_dump(),
                    item_count=overview.item_count,
                )
                for overview in memory_category_service.list_overviews()
            ]
        )

    @router.post("/memory-categories", status_code=status.HTTP_201_CREATED)
    def add_memory_category(request: MemoryCategoryRequest) -> MemoryCategoryResponse:
        """Add an active Memory Category last in the list.

        Args:
            request: The category.

        Returns:
            The saved category.

        Raises:
            HTTPException: 422 if the name or description is blank or the
                name is taken.
        """
        try:
            category = memory_category_service.add(request.to_details())
        except InvalidMemoryCategoryError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_memory_category_response(category)

    @router.put("/memory-categories/{category_id}")
    def update_memory_category(
        admin: Annotated[User, Depends(current_admin)],
        category_id: UUID,
        request: MemoryCategoryRequest,
    ) -> MemoryCategoryResponse:
        """Change a Memory Category's name, description and "always include".

        Args:
            admin: The Admin making the change.
            category_id: The category to change.
            request: Its new name, description and "always include".

        Returns:
            The saved category.

        Raises:
            HTTPException: 404 if there is no such category; 422 if the name
                or description is blank or the name is taken.
        """
        try:
            category = memory_category_service.update(
                admin, category_id, request.to_details()
            )
        except MemoryCategoryNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Memory Category"
            ) from error
        except InvalidMemoryCategoryError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_memory_category_response(category)

    @router.post("/memory-categories/{category_id}/archive")
    def archive_memory_category(category_id: UUID) -> MemoryCategoryResponse:
        """Archive a Memory Category: it keeps its items but gets no new ones.

        Args:
            category_id: The category to archive.

        Returns:
            The saved category.

        Raises:
            HTTPException: 404 if there is no such category.
        """
        return set_archived(category_id, archived=True)

    @router.post("/memory-categories/{category_id}/restore")
    def restore_memory_category(category_id: UUID) -> MemoryCategoryResponse:
        """Restore an archived Memory Category so it gets new items again.

        Args:
            category_id: The category to restore.

        Returns:
            The saved category.

        Raises:
            HTTPException: 404 if there is no such category.
        """
        return set_archived(category_id, archived=False)

    def set_archived(category_id: UUID, archived: bool) -> MemoryCategoryResponse:
        """Archive or restore a Memory Category.

        Args:
            category_id: The category.
            archived: True to archive it, False to restore it.

        Returns:
            The saved category.

        Raises:
            HTTPException: 404 if there is no such category.
        """
        try:
            category = memory_category_service.set_archived(category_id, archived)
        except MemoryCategoryNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Memory Category"
            ) from error
        return to_memory_category_response(category)

    @router.get("/knowledge-documents")
    def list_knowledge_documents() -> KnowledgeDocumentsResponse:
        """List every Knowledge document with its status.

        Returns:
            The documents, newest upload first.
        """
        return KnowledgeDocumentsResponse(
            documents=[
                to_knowledge_document_response(document)
                for document in knowledge_service.list_documents()
            ]
        )

    @router.post("/knowledge-documents", status_code=status.HTTP_201_CREATED)
    def upload_knowledge_document(
        background_tasks: BackgroundTasks,
        file: UploadFile,
        title: Annotated[str, Form()],
        source: Annotated[str, Form()],
        tradition: Annotated[str, Form()],
    ) -> KnowledgeDocumentResponse:
        """Upload a text, Markdown or PDF Knowledge document.

        The document is saved as pending and ingested after the response is
        sent; listing documents shows when it is ready or has failed.

        Args:
            background_tasks: Runs the ingestion after the response.
            file: The uploaded file.
            title: The document's title.
            source: Who wrote or translated it.
            tradition: The tradition it belongs to.

        Returns:
            The pending document.

        Raises:
            HTTPException: 422 if the file type, file or details are not
                valid.
        """
        try:
            uploaded_file = to_knowledge_file(file)
            document = knowledge_service.upload(
                KnowledgeUpload(
                    title=title,
                    source=source,
                    tradition=tradition,
                    file_name=uploaded_file.file_name,
                    file_type=uploaded_file.file_type,
                    content=uploaded_file.content,
                )
            )
        except InvalidKnowledgeDocumentError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        background_tasks.add_task(knowledge_service.ingest, document.id)
        return to_knowledge_document_response(document)

    @router.get("/knowledge-documents/{document_id}")
    def get_knowledge_document(document_id: UUID) -> KnowledgeDocumentWithTextResponse:
        """Show a Knowledge document with the text replies draw on.

        Args:
            document_id: The document to show.

        Returns:
            The document and its text.

        Raises:
            HTTPException: 404 if there is no such document.
        """
        try:
            document_with_text = knowledge_service.get_document(document_id)
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        return to_knowledge_document_with_text_response(document_with_text)

    @router.patch("/knowledge-documents/{document_id}")
    def update_knowledge_document_details(
        document_id: UUID, request: KnowledgeDetailsRequest
    ) -> KnowledgeDocumentWithTextResponse:
        """Change a Knowledge document's title, source or tradition.

        Takes effect straight away, with no re-indexing.

        Args:
            document_id: The document to change.
            request: The details to change.

        Returns:
            The saved document and its text.

        Raises:
            HTTPException: 404 if there is no such document; 422 if a given
                detail is blank.
        """
        try:
            document_with_text = knowledge_service.update_details(
                document_id,
                KnowledgeDetailsChange(
                    title=request.title,
                    source=request.source,
                    tradition=request.tradition,
                ),
            )
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        except InvalidKnowledgeDocumentError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        return to_knowledge_document_with_text_response(document_with_text)

    @router.put("/knowledge-documents/{document_id}/text")
    def save_knowledge_document_text(
        background_tasks: BackgroundTasks,
        document_id: UUID,
        request: KnowledgeTextRequest,
    ) -> KnowledgeDocumentWithTextResponse:
        """Save a Knowledge document's edited text and index it again.

        The document is pending until it is indexed after the response.

        Args:
            background_tasks: Runs the indexing after the response.
            document_id: The document to change.
            request: Its new text.

        Returns:
            The pending document and its text.

        Raises:
            HTTPException: 404 if there is no such document; 409 if its file
                is still being read; 422 if the text is blank.
        """
        try:
            document_with_text = knowledge_service.save_text(document_id, request.text)
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        except KnowledgeFileStillBeingReadError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "The file is still being read. Try again when it’s done.",
            ) from error
        except InvalidKnowledgeDocumentError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        background_tasks.add_task(knowledge_service.ingest, document_id)
        return to_knowledge_document_with_text_response(document_with_text)

    @router.put("/knowledge-documents/{document_id}/file")
    def replace_knowledge_document_file(
        background_tasks: BackgroundTasks, document_id: UUID, file: UploadFile
    ) -> KnowledgeDocumentWithTextResponse:
        """Replace a Knowledge document's file with a text, Markdown or PDF file.

        The document keeps its ID, details and added date, and is pending
        until the new file is read and indexed after the response.

        Args:
            background_tasks: Runs the reading and indexing after the response.
            document_id: The document to change.
            file: The new file.

        Returns:
            The pending document, with no text yet.

        Raises:
            HTTPException: 404 if there is no such document; 409 if its last
                file is still being read; 422 if the file type or file is not
                valid.
        """
        try:
            document_with_text = knowledge_service.replace_file(
                document_id, to_knowledge_file(file)
            )
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        except KnowledgeFileStillBeingReadError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "The file is still being read. Try again when it’s done.",
            ) from error
        except InvalidKnowledgeDocumentError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
            ) from error
        background_tasks.add_task(knowledge_service.ingest, document_id)
        return to_knowledge_document_with_text_response(document_with_text)

    @router.post("/knowledge-documents/{document_id}/retry")
    def retry_knowledge_document(
        background_tasks: BackgroundTasks, document_id: UUID
    ) -> KnowledgeDocumentResponse:
        """Ingest a failed Knowledge document again.

        Args:
            background_tasks: Runs the ingestion after the response.
            document_id: The document to retry.

        Returns:
            The pending document.

        Raises:
            HTTPException: 404 if there is no such document; 409 if it has
                not failed.
        """
        try:
            document = knowledge_service.retry(document_id)
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        except KnowledgeNotRetryableError as error:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Only a failed document can be retried."
            ) from error
        background_tasks.add_task(knowledge_service.ingest, document.id)
        return to_knowledge_document_response(document)

    @router.delete(
        "/knowledge-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
    )
    def delete_knowledge_document(document_id: UUID) -> Response:
        """Remove a Knowledge document and its chunks.

        Args:
            document_id: The document to remove.

        Returns:
            An empty response.

        Raises:
            HTTPException: 404 if there is no such document.
        """
        try:
            knowledge_service.delete(document_id)
        except KnowledgeDocumentNotFoundError as error:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such Knowledge document"
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
