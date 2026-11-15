from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, UploadFile, status
from pydantic import BaseModel

from companion.core.evals.case_editing import IMAGE_MAX_BYTES, EvalCaseService
from companion.core.evals.case_shapes import FieldKind, FormShape, ShapeField
from companion.core.evals.judge_settings import JudgeSettingsService
from companion.core.evals.models import EvalName, StoredEvalCase
from companion.core.models import User


class ChoiceOptionResponse(BaseModel):
    """One value a choice field can hold."""

    value: str | bool
    label: str


class ShapeFieldResponse(BaseModel):
    """One field of a form: what it holds and what it means."""

    name: str
    label: str
    description: str
    kind: FieldKind
    required: bool
    options: list[ChoiceOptionResponse]
    fields: list["ShapeFieldResponse"]
    unique_by: str
    item_label: str
    minimum: int | None
    default: Any


class ShapeSectionResponse(BaseModel):
    """A part of a form."""

    title: str
    description: str
    fields: list[ShapeFieldResponse]


class FormShapeResponse(BaseModel):
    """The fields a case, or the Judge's settings, is made of, in sections."""

    sections: list[ShapeSectionResponse]


class EvalCaseShapesResponse(BaseModel):
    """Every Eval's case shape, which draws its form."""

    shapes: dict[EvalName, FormShapeResponse]


class EvalCaseResponse(BaseModel):
    """An Eval Case as Admins see it."""

    key: str
    eval: EvalName
    content: dict[str, Any]
    archived: bool
    edited: bool
    updated_at: datetime
    updated_by_name: str | None


class EvalCasesResponse(BaseModel):
    """One Eval's cases, archived ones too, in the order added."""

    cases: list[EvalCaseResponse]


class AddEvalCaseRequest(BaseModel):
    """A new case an Admin wrote."""

    key: str
    eval: EvalName
    content: dict[str, Any]


class EditEvalCaseRequest(BaseModel):
    """A case's new content."""

    content: dict[str, Any]


class DuplicateEvalCaseRequest(BaseModel):
    """The key of a case's copy."""

    key: str


class EvalImageResponse(BaseModel):
    """An uploaded test image, by the name cases refer to it by."""

    name: str


class JudgeSettingsResponse(BaseModel):
    """The Judge's settings and the form that edits them."""

    shape: FormShapeResponse
    values: dict[str, Any]


class SaveJudgeSettingsRequest(BaseModel):
    """The Judge's new settings."""

    values: dict[str, Any]


def to_field_response(shape_field: ShapeField) -> ShapeFieldResponse:
    """Describe one field of a form for the Dashboard.

    Args:
        shape_field: The field.

    Returns:
        The response.
    """
    return ShapeFieldResponse(
        name=shape_field.name,
        label=shape_field.label,
        description=shape_field.description,
        kind=shape_field.kind,
        required=shape_field.required,
        options=[
            ChoiceOptionResponse(value=option.value, label=option.label)
            for option in shape_field.options
        ],
        fields=[to_field_response(inner) for inner in shape_field.fields],
        unique_by=shape_field.unique_by,
        item_label=shape_field.item_label,
        minimum=shape_field.minimum,
        default=shape_field.default,
    )


def to_shape_response(shape: FormShape) -> FormShapeResponse:
    """Describe a form for the Dashboard to draw.

    Args:
        shape: The form's shape.

    Returns:
        The response.
    """
    return FormShapeResponse(
        sections=[
            ShapeSectionResponse(
                title=section.title,
                description=section.description,
                fields=[to_field_response(inner) for inner in section.fields],
            )
            for section in shape.sections
        ]
    )


def to_case_response(stored: StoredEvalCase) -> EvalCaseResponse:
    """Describe an Eval Case for the Dashboard.

    Args:
        stored: The case.

    Returns:
        The response.
    """
    return EvalCaseResponse(
        key=stored.case.key,
        eval=stored.case.eval,
        content=stored.case.content,
        archived=stored.case.archived,
        edited=stored.edited,
        updated_at=stored.updated_at,
        updated_by_name=stored.updated_by_name,
    )


def build_eval_case_api_router(
    current_admin: Callable[..., User],
    eval_case_service: EvalCaseService,
    judge_settings_service: JudgeSettingsService,
) -> APIRouter:
    """Build the admin routes for Eval Cases, their images and the Judge.

    Every route refuses anyone who is not an Admin. A save that doesn't fit
    its form answers 422 with `fields`, a message per field path.

    Args:
        current_admin: The dependency that lets only Admins through.
        eval_case_service: Adds, edits, duplicates and archives Eval Cases.
        judge_settings_service: Reads and saves the Judge's settings.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    @router.get("/eval-case-shapes")
    def list_eval_case_shapes() -> EvalCaseShapesResponse:
        """Give every Eval's case shape, which draws its form.

        Returns:
            The shapes.
        """
        return EvalCaseShapesResponse(
            shapes={
                name: to_shape_response(shape)
                for name, shape in eval_case_service.shapes().items()
            }
        )

    @router.get("/eval-cases")
    def list_eval_cases(eval: EvalName) -> EvalCasesResponse:
        """List one Eval's cases, archived ones too.

        Args:
            eval: The Eval.

        Returns:
            The cases, in the order added.
        """
        return EvalCasesResponse(
            cases=[
                to_case_response(case) for case in eval_case_service.list_cases(eval)
            ]
        )

    @router.post("/eval-cases", status_code=status.HTTP_201_CREATED)
    def add_eval_case(
        request: AddEvalCaseRequest, admin: Annotated[User, Depends(current_admin)]
    ) -> EvalCaseResponse:
        """Add a case; the next run of its Eval includes it.

        Args:
            request: Its key, Eval and content.
            admin: The Admin adding it.

        Returns:
            The case.

        Raises:
            CoreError: 422 if the key or content doesn't fit.
        """
        return to_case_response(
            eval_case_service.add_case(
                admin, request.key, request.eval, request.content
            )
        )

    @router.get("/eval-cases/{key}")
    def open_eval_case(key: str) -> EvalCaseResponse:
        """Open one case.

        Args:
            key: Its key.

        Returns:
            The case.

        Raises:
            CoreError: 404 if no case has the key.
        """
        return to_case_response(eval_case_service.get_case(key))

    @router.put("/eval-cases/{key}")
    def edit_eval_case(
        key: str,
        request: EditEvalCaseRequest,
        admin: Annotated[User, Depends(current_admin)],
    ) -> EvalCaseResponse:
        """Change a case; the next run uses it, old runs keep theirs.

        Args:
            key: Its key.
            request: Its new content.
            admin: The Admin changing it.

        Returns:
            The case.

        Raises:
            CoreError: 404 if no case has the key, 409 if it is archived,
                422 if the content doesn't fit.
        """
        return to_case_response(
            eval_case_service.edit_case(admin, key, request.content)
        )

    @router.post("/eval-cases/{key}/duplicate", status_code=status.HTTP_201_CREATED)
    def duplicate_eval_case(
        key: str,
        request: DuplicateEvalCaseRequest,
        admin: Annotated[User, Depends(current_admin)],
    ) -> EvalCaseResponse:
        """Copy a case under a new key.

        Args:
            key: The case to copy.
            request: The copy's key.
            admin: The Admin copying it.

        Returns:
            The copy.

        Raises:
            CoreError: 404 if no case has the key, 422 if the new key
                doesn't fit or is taken.
        """
        return to_case_response(
            eval_case_service.duplicate_case(admin, key, request.key)
        )

    @router.post("/eval-cases/{key}/archive")
    def archive_eval_case(
        key: str, admin: Annotated[User, Depends(current_admin)]
    ) -> EvalCaseResponse:
        """Archive a case: new runs leave it out, old runs still show it.

        Args:
            key: Its key.
            admin: The Admin archiving it.

        Returns:
            The case.

        Raises:
            CoreError: 404 if no case has the key.
        """
        return to_case_response(eval_case_service.archive_case(admin, key))

    @router.post("/eval-images", status_code=status.HTTP_201_CREATED)
    def upload_eval_image(file: UploadFile) -> EvalImageResponse:
        """Keep an uploaded test image for a photo case to send.

        Args:
            file: A PNG, JPEG or WebP image of at most 5 MB.

        Returns:
            The name cases refer to it by.

        Raises:
            CoreError: 422 if it isn't such an image.
        """
        image = eval_case_service.add_image(
            file.filename or "",
            file.file.read(IMAGE_MAX_BYTES + 1),
            file.content_type or "",
        )
        return EvalImageResponse(name=image.name)

    @router.get("/eval-images/{name}")
    def get_eval_image(name: str) -> Response:
        """Return a test image, to show beside its case.

        Args:
            name: Its name.

        Returns:
            The image.

        Raises:
            CoreError: 404 if no image has the name.
        """
        image = eval_case_service.get_image(name)
        return Response(
            content=image.content,
            media_type=image.media_type,
            headers={"Cache-Control": "private, max-age=86400"},
        )

    @router.get("/eval-judge")
    def open_judge_settings() -> JudgeSettingsResponse:
        """Open the Judge's settings and the form that edits them.

        Returns:
            The form and the settings.
        """
        return JudgeSettingsResponse(
            shape=to_shape_response(judge_settings_service.shape()),
            values=judge_settings_service.values(),
        )

    @router.put("/eval-judge")
    def save_judge_settings(
        request: SaveJudgeSettingsRequest,
        admin: Annotated[User, Depends(current_admin)],
    ) -> JudgeSettingsResponse:
        """Save the Judge's settings; the next run uses them.

        Args:
            request: Every setting's new value.
            admin: The Admin changing them.

        Returns:
            The form and the settings after the change.

        Raises:
            CoreError: 422 if a value doesn't fit.
        """
        values = judge_settings_service.save(admin, request.values)
        return JudgeSettingsResponse(
            shape=to_shape_response(judge_settings_service.shape()), values=values
        )

    return router
