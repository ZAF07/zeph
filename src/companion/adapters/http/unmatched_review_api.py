from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from companion.adapters.http.thought_experiment_api import PatternTypeChoiceResponse
from companion.core.models import UnmatchedMark, User
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.unmatched_review import ReviewedEntry, UnmatchedReviewService


class UnmatchedEntryResponse(BaseModel):
    """Something that keeps turning up unmatched, as Admins see it.

    It holds a general description and a count of Users: nothing a User
    said and nothing that names one.
    """

    id: str
    description: str
    user_count: int
    mark: UnmatchedMark
    folded_into_pattern_type_id: str | None
    dropped_before: bool


class UnmatchedEntriesResponse(BaseModel):
    """The unmatched entries, most Users first, and the Pattern Types to fold into."""

    entries: list[UnmatchedEntryResponse]
    pattern_types: list[PatternTypeChoiceResponse]


class UnmatchedMarkRequest(BaseModel):
    """What an Admin decides about an unmatched entry.

    `pattern_type_id` is the Pattern Type it is folded into, used only
    when the mark is folded.
    """

    mark: UnmatchedMark
    pattern_type_id: str | None = None


def to_unmatched_entry_response(entry: ReviewedEntry) -> UnmatchedEntryResponse:
    """Turn an unmatched entry into its API response.

    Args:
        entry: The entry as an Admin reads it.

    Returns:
        The response.
    """
    return UnmatchedEntryResponse(
        id=str(entry.id),
        description=entry.description,
        user_count=entry.user_count,
        mark=entry.mark,
        folded_into_pattern_type_id=entry.folded_into_pattern_type_id,
        dropped_before=entry.dropped_before,
    )


def build_unmatched_review_api_router(
    current_admin: Callable[..., User],
    unmatched_review_service: UnmatchedReviewService,
    pattern_catalog_service: PatternCatalogService,
) -> APIRouter:
    """Build the routes Admins review unmatched entries with.

    Args:
        current_admin: The dependency that lets only Admins through.
        unmatched_review_service: Lists and marks the entries.
        pattern_catalog_service: Reads the Pattern Types to fold into.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    @router.get("/unmatched-patterns")
    def list_unmatched_entries(
        mark: UnmatchedMark | None = None,
    ) -> UnmatchedEntriesResponse:
        """List what keeps turning up unmatched, most Users first.

        Args:
            mark: Only entries that read as this mark now; all when left out.

        Returns:
            The entries that appear for at least one User, and the
            catalog's Pattern Types by ID.
        """
        return UnmatchedEntriesResponse(
            entries=[
                to_unmatched_entry_response(entry)
                for entry in unmatched_review_service.list_entries(mark)
            ],
            pattern_types=sorted(
                (
                    PatternTypeChoiceResponse(
                        id=entry.pattern_type.id, name=entry.pattern_type.name
                    )
                    for entry in pattern_catalog_service.catalog()
                ),
                key=lambda choice: choice.id,
            ),
        )

    @router.put("/unmatched-patterns/{entry_id}/mark")
    def mark_unmatched_entry(
        entry_id: UUID, request: UnmatchedMarkRequest
    ) -> UnmatchedEntryResponse:
        """Mark an entry: new Pattern Type, folded into one, dropped or to review.

        Args:
            entry_id: The entry to mark.
            request: The mark, and the Pattern Type when folded.

        Returns:
            The entry as it reads now.

        Raises:
            CoreError: 404 if there is no such entry; 422 if it is folded
                into no Pattern Type in the catalog.
        """
        return to_unmatched_entry_response(
            unmatched_review_service.mark(
                entry_id, request.mark, request.pattern_type_id
            )
        )

    return router
