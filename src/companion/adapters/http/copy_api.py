from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from companion.core.copy import CopyService
from companion.core.models import CopyTab, User


class CopyResponse(BaseModel):
    """Every Copy slot's current text, by key, for the website."""

    texts: dict[str, str]


class CopySlotResponse(BaseModel):
    """A Copy slot as Admins see it on the Copy page."""

    key: str
    name: str
    text: str
    max_length: int
    placeholders: list[str]
    updated_at: datetime
    updated_by: str | None


class CopyTabResponse(BaseModel):
    """One tab of the Copy page, with its slots in page order."""

    tab: str
    name: str
    slots: list[CopySlotResponse]


class CopyPageResponse(BaseModel):
    """The Copy page: its tabs in order."""

    tabs: list[CopyTabResponse]


class CopyTabSaveRequest(BaseModel):
    """New texts for some of a tab's slots, by key; others stay as they are."""

    texts: dict[str, str]


def to_copy_page_response(tabs: list[CopyTab]) -> CopyPageResponse:
    """Describe the Copy page for the admin area.

    Args:
        tabs: The tabs, each with its slots.

    Returns:
        The response body.
    """
    return CopyPageResponse(
        tabs=[
            CopyTabResponse(
                tab=tab.tab,
                name=tab.name,
                slots=[
                    CopySlotResponse(
                        key=slot.key,
                        name=slot.name,
                        text=slot.text,
                        max_length=slot.max_length,
                        placeholders=list(slot.placeholders),
                        updated_at=slot.updated_at,
                        updated_by=slot.updated_by_name,
                    )
                    for slot in tab.slots
                ],
            )
            for tab in tabs
        ]
    )


def build_copy_api_router(
    current_admin: Callable[..., User], copy_service: CopyService
) -> APIRouter:
    """Build the Copy routes: a public read, and the Admin page and save.

    Args:
        current_admin: The dependency that lets only Admins through.
        copy_service: Reads and saves Copy.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api")

    @router.get("/copy")
    def get_copy() -> CopyResponse:
        """Return every slot's text; needs no sign-in, so visitors see it.

        Returns:
            Each slot's current text, by key.
        """
        return CopyResponse(texts=copy_service.read_all())

    @router.get("/admin/copy", dependencies=[Depends(current_admin)])
    def get_copy_page() -> CopyPageResponse:
        """Return the Copy page: each tab with its slots in page order.

        Returns:
            The tabs.
        """
        return to_copy_page_response(copy_service.copy_page())

    @router.put("/admin/copy/{tab}")
    def save_copy_tab(
        tab: str,
        admin: Annotated[User, Depends(current_admin)],
        request: CopyTabSaveRequest,
    ) -> CopyPageResponse:
        """Save one tab's changed texts, all together or not at all.

        Args:
            tab: The key of the tab being saved.
            admin: The Admin making the change.
            request: The new texts, by slot key.

        Returns:
            The Copy page after the save.

        Raises:
            CoreError: 404 if there is no such tab; 422 with a reason per
                slot if any text can't be saved.
        """
        return to_copy_page_response(copy_service.save_tab(admin, tab, request.texts))

    return router
