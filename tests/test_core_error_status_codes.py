from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from companion.adapters.http.errors import add_core_error_handlers
from companion.core.admin_users import (
    LAST_ADMIN_DEMOTION,
    LastAdminError,
    UserNotFoundError,
)
from companion.core.check_in_kinds import (
    CheckInKindNotFoundError,
    InvalidCheckInKindError,
)
from companion.core.errors import (
    ConflictError,
    CoreError,
    InvalidError,
    NotAllowedError,
    NotFoundError,
    OutsideServiceError,
)
from companion.core.features import FeatureNotAvailableError
from companion.core.helplines import (
    FallbackHelplineError,
    HelplineNotFoundError,
    InvalidHelplineError,
)
from companion.core.knowledge import (
    InvalidKnowledgeDocumentError,
    KnowledgeDocumentNotFoundError,
    KnowledgeFileStillBeingReadError,
    KnowledgeNotRetryableError,
)
from companion.core.memory_categories import (
    InvalidMemoryCategoryError,
    MemoryCategoryNotFoundError,
    RequiredMemoryCategoryError,
)
from companion.core.models import Feature
from companion.core.personal_stickers import PersonalStickerNotFoundError
from companion.core.photos import SharedPhotoNotFoundError
from companion.core.platform_settings import InvalidSettingError
from companion.core.safeguard import InvalidEventFilterError
from companion.core.stickers import (
    InvalidStickerError,
    StickerNotFoundError,
    StickerSetNotFoundError,
    StickerSetUnavailableError,
)
from companion.core.telegram_connection import OnboardingNotFinishedError
from companion.core.user_data import LAST_ADMIN_ACCOUNT_DELETION
from companion.core.user_memory import (
    ConversationSummaryNotFoundError,
    MemoryNotFoundError,
)
from companion.core.users import InvalidProfileError

ERRORS_WITH_STATUS_AND_DETAIL: list[tuple[CoreError, type[CoreError], int, str]] = [
    (UserNotFoundError(uuid4()), NotFoundError, 404, "No such User"),
    (MemoryNotFoundError(), NotFoundError, 404, "Memory not found"),
    (
        ConversationSummaryNotFoundError(),
        NotFoundError,
        404,
        "Conversation Summary not found",
    ),
    (SharedPhotoNotFoundError(uuid4()), NotFoundError, 404, "Shared Photo not found"),
    (
        PersonalStickerNotFoundError(uuid4()),
        NotFoundError,
        404,
        "Personal Sticker not found",
    ),
    (HelplineNotFoundError(uuid4()), NotFoundError, 404, "No such Helpline"),
    (
        MemoryCategoryNotFoundError(uuid4()),
        NotFoundError,
        404,
        "No such Memory Category",
    ),
    (CheckInKindNotFoundError(uuid4()), NotFoundError, 404, "No such Check-in Kind"),
    (StickerNotFoundError(uuid4()), NotFoundError, 404, "No such sticker"),
    (
        StickerSetNotFoundError("cats"),
        NotFoundError,
        404,
        "There is no sticker set called “cats”.",
    ),
    (
        KnowledgeDocumentNotFoundError(uuid4()),
        NotFoundError,
        404,
        "No such Knowledge document",
    ),
    (
        FeatureNotAvailableError(Feature.CHECK_INS),
        NotAllowedError,
        403,
        "Not available on your account",
    ),
    (
        InvalidProfileError("Name is required."),
        InvalidError,
        422,
        "Name is required.",
    ),
    (InvalidSettingError("Bad value."), InvalidError, 422, "Bad value."),
    (
        InvalidHelplineError("A Helpline needs a name."),
        InvalidError,
        422,
        "A Helpline needs a name.",
    ),
    (
        InvalidEventFilterError("Filter by a crisis risk type."),
        InvalidError,
        422,
        "Filter by a crisis risk type.",
    ),
    (InvalidMemoryCategoryError("Needs a name."), InvalidError, 422, "Needs a name."),
    (InvalidCheckInKindError("Needs a name."), InvalidError, 422, "Needs a name."),
    (
        InvalidStickerError("Enter a sticker set name."),
        InvalidError,
        422,
        "Enter a sticker set name.",
    ),
    (
        InvalidKnowledgeDocumentError("The file is empty."),
        InvalidError,
        422,
        "The file is empty.",
    ),
    (
        LastAdminError(LAST_ADMIN_DEMOTION),
        ConflictError,
        409,
        "This is the last Admin. Make someone else an Admin first.",
    ),
    (
        LastAdminError(LAST_ADMIN_ACCOUNT_DELETION),
        ConflictError,
        409,
        "You’re the only Admin. Make someone else an Admin before deleting "
        "your account.",
    ),
    (
        OnboardingNotFinishedError(),
        ConflictError,
        409,
        "Finish onboarding before connecting Telegram.",
    ),
    (
        FallbackHelplineError(),
        ConflictError,
        409,
        "The international fallback can't be removed, only edited.",
    ),
    (
        RequiredMemoryCategoryError("Goals is used by the Home page."),
        ConflictError,
        409,
        "Goals is used by the Home page.",
    ),
    (
        KnowledgeFileStillBeingReadError(uuid4()),
        ConflictError,
        409,
        "The file is still being read. Try again when it’s done.",
    ),
    (
        KnowledgeNotRetryableError(uuid4()),
        ConflictError,
        409,
        "Only a failed document can be retried.",
    ),
    (
        StickerSetUnavailableError("cats"),
        OutsideServiceError,
        502,
        "Telegram didn’t respond. Please try again.",
    ),
]


def client_raising(error: Exception) -> TestClient:
    """Build an app with the core error handlers and one route raising the error."""
    app = FastAPI()
    add_core_error_handlers(app)

    @app.get("/raise")
    def raise_error() -> None:
        raise error

    return TestClient(app)


@pytest.mark.parametrize(
    ("error", "base", "status_code", "detail"),
    ERRORS_WITH_STATUS_AND_DETAIL,
    ids=[type(case[0]).__name__ for case in ERRORS_WITH_STATUS_AND_DETAIL],
)
def test_each_core_error_has_a_base_and_keeps_its_status_and_body(
    error: CoreError, base: type[CoreError], status_code: int, detail: str
) -> None:
    assert isinstance(error, base)

    response = client_raising(error).get("/raise")

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


def test_a_new_error_gets_its_status_from_its_base_class() -> None:
    class ThingNotFoundError(NotFoundError):
        """A not-found error no handler names."""

        shown_message = "No such thing"

    response = client_raising(ThingNotFoundError()).get("/raise")

    assert response.status_code == 404
    assert response.json() == {"detail": "No such thing"}
