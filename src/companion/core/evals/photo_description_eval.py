from uuid import UUID

from companion.core.evals.cases import PhotoDescriptionCase
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.ports import EvalCompanion, EvalSetupError
from companion.core.models import MessageDirection
from companion.core.ports import Repositories

PHOTO_DESCRIPTION_START = "[photo: "


def saved_photo_message(repositories: Repositories, user_id: UUID) -> str:
    """Read the one photo message the User sent, as the Companion reads it.

    Args:
        repositories: The Eval database's repositories.
        user_id: The User's ID.

    Returns:
        The saved message, holding the photo's description.

    Raises:
        EvalSetupError: If there isn't exactly one incoming message.
    """
    conversation = repositories.conversations.get_latest_for_user(user_id)
    messages = (
        repositories.conversations.list_messages(conversation.id)
        if conversation
        else []
    )
    incoming = [
        message
        for message in messages
        if message.direction == MessageDirection.INCOMING
    ]
    if len(incoming) != 1:
        raise EvalSetupError(f"Expected one incoming message, found {len(incoming)}")
    return incoming[0].content


def check_photo_description_case(
    case: PhotoDescriptionCase, companion: EvalCompanion
) -> CaseCheckResult:
    """Send a test image and check its description leaves out what it must.

    Args:
        case: The test image and the text it must leave out.
        companion: The app on the Eval database.

    Returns:
        One check; its facts hold the description.
    """
    user_id = companion.connect_user()

    companion.send_photo(case.photo, caption="")

    description = saved_photo_message(companion.repositories, user_id)
    leaked = [
        text for text in case.must_leave_out if text.lower() in description.lower()
    ]
    described = description.startswith(PHOTO_DESCRIPTION_START)
    if not described:
        check = Check("described", False, f"not a photo description: {description}")
    elif leaked:
        check = Check("left out", False, f"leaked {', '.join(leaked)}")
    else:
        check = Check("left out", True, f"left out {', '.join(case.must_leave_out)}")
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if check.passed else CaseOutcome.FAIL,
        checks=[check],
        facts={"description": description},
    )
