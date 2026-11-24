from collections.abc import Callable
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from companion.core.models import (
    CatalogPatternType,
    ExcludedEvidence,
    PatternArea,
    PatternSign,
    PatternTypeStatus,
    SignPart,
    SignStrength,
    User,
)
from companion.core.pattern_catalog import PatternCatalogService


class PatternSignResponse(BaseModel):
    """One sign for or against a Pattern Type."""

    id: str
    text: str
    strength: SignStrength
    part: SignPart


class LookAlikeResponse(BaseModel):
    """Something a Pattern Type can be mistaken for.

    `pattern_type_id` is None when the look-alike is not a Pattern Type;
    `name` is always what to call it.
    """

    pattern_type_id: str | None
    name: str
    tells_apart: str


class PatternExclusionResponse(BaseModel):
    """A time in a User's life when a Pattern Type must not be shared."""

    text: str
    evidence: ExcludedEvidence


class PatternTypeNumbersResponse(BaseModel):
    """A Pattern Type's own numbers."""

    situations_needed: int
    base_rate: float


class PatternTypeResponse(BaseModel):
    """A Pattern Type in the catalog now, with all its details."""

    id: str
    version: str
    area: PatternArea
    name: str
    definition: str
    if_situation: str
    then_behaviour: str
    function: str
    frameworks: list[str]
    signs: list[PatternSignResponse]
    signs_against: list[PatternSignResponse]
    look_alikes: list[LookAlikeResponse]
    anyone_would: str | None
    exclusions: list[PatternExclusionResponse]
    approved_wording: str
    prediction_wording: str
    numbers: PatternTypeNumbersResponse
    status: PatternTypeStatus
    approved_by: str | None
    approved_on: date | None
    loaded_at: datetime
    other_versions: list[str]


class PatternCatalogResponse(BaseModel):
    """The Pattern Catalog: every Pattern Type, by area and then ID."""

    pattern_types: list[PatternTypeResponse]


def to_sign_response(sign: PatternSign) -> PatternSignResponse:
    """Describe a sign for the admin area.

    Args:
        sign: The sign.

    Returns:
        The response body.
    """
    return PatternSignResponse(
        id=sign.id, text=sign.text, strength=sign.strength, part=sign.part
    )


def to_pattern_catalog_response(
    catalog: list[CatalogPatternType],
) -> PatternCatalogResponse:
    """Describe the Pattern Catalog for the admin area.

    Args:
        catalog: Every Pattern Type in the catalog now.

    Returns:
        The response body, each look-alike that is a Pattern Type carrying
        that Pattern Type's name.
    """
    name_by_id = {entry.pattern_type.id: entry.pattern_type.name for entry in catalog}
    return PatternCatalogResponse(
        pattern_types=[
            PatternTypeResponse(
                id=entry.pattern_type.id,
                version=entry.pattern_type.version,
                area=entry.pattern_type.area,
                name=entry.pattern_type.name,
                definition=entry.pattern_type.definition,
                if_situation=entry.pattern_type.if_situation,
                then_behaviour=entry.pattern_type.then_behaviour,
                function=entry.pattern_type.function,
                frameworks=list(entry.pattern_type.frameworks),
                signs=[to_sign_response(sign) for sign in entry.pattern_type.signs],
                signs_against=[
                    to_sign_response(sign) for sign in entry.pattern_type.signs_against
                ],
                look_alikes=[
                    LookAlikeResponse(
                        pattern_type_id=look_alike.pattern_type_id,
                        name=look_alike.name
                        or name_by_id[look_alike.pattern_type_id or ""],
                        tells_apart=look_alike.tells_apart,
                    )
                    for look_alike in entry.pattern_type.look_alikes
                ],
                anyone_would=entry.pattern_type.anyone_would,
                exclusions=[
                    PatternExclusionResponse(
                        text=exclusion.text, evidence=exclusion.evidence
                    )
                    for exclusion in entry.pattern_type.exclusions
                ],
                approved_wording=entry.pattern_type.approved_wording,
                prediction_wording=entry.pattern_type.prediction_wording,
                numbers=PatternTypeNumbersResponse(
                    situations_needed=entry.pattern_type.numbers.situations_needed,
                    base_rate=entry.pattern_type.numbers.base_rate,
                ),
                status=entry.pattern_type.status,
                approved_by=entry.pattern_type.approved_by,
                approved_on=entry.pattern_type.approved_on,
                loaded_at=entry.loaded_at,
                other_versions=list(entry.other_versions),
            )
            for entry in catalog
        ]
    )


def build_pattern_catalog_api_router(
    current_admin: Callable[..., User],
    pattern_catalog_service: PatternCatalogService,
) -> APIRouter:
    """Build the Pattern Catalog route: Admins read it and can't change it.

    Pattern Types change only through their files and a deploy (ADR-0025),
    so there is no route that saves one.

    Args:
        current_admin: The dependency that lets only Admins through.
        pattern_catalog_service: Reads the Pattern Catalog.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    @router.get("/pattern-catalog")
    def get_pattern_catalog() -> PatternCatalogResponse:
        """Return every Pattern Type in the catalog now, with all its details.

        Returns:
            The Pattern Types, by area and then ID.
        """
        return to_pattern_catalog_response(pattern_catalog_service.catalog())

    return router
