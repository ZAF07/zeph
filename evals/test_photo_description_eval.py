import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.models import MessageDirection
from evals.cases import CASES_DIR, PhotoDescriptionCase, load_photo_description_cases
from evals.photos import send_test_photo
from evals.report import EvalReport, PhotoDescriptionResult
from tests.fakes import FakeAuthVerifier, FakeChatChannel
from tests.telegram_helpers import connect_telegram

pytestmark = pytest.mark.eval

PHOTO_DESCRIPTION_CASES = load_photo_description_cases(
    CASES_DIR / "photo_descriptions.yaml"
)


def saved_photo_message(engine: Engine) -> str:
    """Read the one photo message the User sent, as the Companion reads it.

    Args:
        engine: The eval database.

    Returns:
        The saved message, holding the photo's description.
    """
    repositories = build_postgres_repositories(engine)
    [user] = [overview.user for overview in repositories.users.list_overviews()]
    conversation = repositories.conversations.get_latest_for_user(user.id)
    assert conversation is not None
    [incoming] = [
        message
        for message in repositories.conversations.list_messages(conversation.id)
        if message.direction == MessageDirection.INCOMING
    ]
    return incoming.content


@pytest.mark.parametrize(
    "case", PHOTO_DESCRIPTION_CASES, ids=[case.id for case in PHOTO_DESCRIPTION_CASES]
)
def test_a_photo_description_leaves_out_numbers_and_passwords(
    case: PhotoDescriptionCase,
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    eval_report: EvalReport,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    send_test_photo(client, chat_channel, case.photo, caption="")

    description = saved_photo_message(engine)
    leaked = [
        text for text in case.must_leave_out if text.lower() in description.lower()
    ]
    eval_report.photo_descriptions.append(
        PhotoDescriptionResult(case, description, leaked)
    )
    assert description.startswith("[photo: "), description
    assert not leaked, description
