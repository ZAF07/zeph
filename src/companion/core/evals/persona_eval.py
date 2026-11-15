from companion.core.evals.cases import PersonaConversation, PersonaMessage
from companion.core.evals.judge import RuleVerdict, judge_persona_rules
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.ports import EvalCompanion, EvalSetupError

SEND_PHOTO_TOOL = "send_photo"


def send_and_collect_replies(
    companion: EvalCompanion,
    message: PersonaMessage,
    shared_photo_descriptions: dict[str, str],
) -> list[str]:
    """Send one scripted message and return Zeph's replies.

    Args:
        companion: The app on the Eval database.
        message: The scripted message, text or a photo of a test image.
        shared_photo_descriptions: What each of the person's Shared Photos
            shows, by file ID.

    Returns:
        Zeph's texts in reply, in order, then a line for any photo it sent
        back.
    """
    if message.photo:
        replies = companion.send_photo(message.photo.file_name, message.text)
    else:
        replies = companion.send_text(message.text)
    photo_lines = [
        "(sends back the person's photo that shows: "
        f"{shared_photo_descriptions[file_id]})"
        for file_id in replies.photo_file_ids
    ]
    return replies.texts + photo_lines


def person_line(message: PersonaMessage) -> str:
    """Write the person's message as one line of the Judge's transcript.

    Args:
        message: The scripted message.

    Returns:
        The line, e.g. "Person: hey", or for a photo what it really shows.
    """
    if message.photo:
        caption = f" with the caption: {message.text}" if message.text else ""
        return f"Person: (sends a photo that shows: {message.photo.shows}){caption}"
    return f"Person: {message.text}"


def verdict_check(verdict: RuleVerdict, group: str = "") -> Check:
    """Turn the Judge's verdict on a rule into a check.

    Args:
        verdict: The verdict.
        group: What the rule was checked on, if the case has several parts.

    Returns:
        The check, named after the rule, with the Judge's reason.
    """
    return Check(
        name=verdict.rule, passed=verdict.passed, detail=verdict.reason, group=group
    )


def check_persona_case(
    conversation: PersonaConversation, companion: EvalCompanion
) -> CaseCheckResult:
    """Send a scripted conversation and have the Judge check its rules.

    Args:
        conversation: The scripted conversation and its rules.
        companion: The app on the Eval database.

    Returns:
        One check per rule; a failed case notes the whole conversation.

    Raises:
        EvalSetupError: If the case has Shared Photos but the reply was
            never offered the tool to send one, so it tested nothing.
    """
    companion.connect_user()
    if not conversation.photo_viewing:
        companion.turn_photo_viewing_off()
    shared_photo_descriptions = {}
    for number, photo in enumerate(conversation.shared_photos, start=1):
        file_id = f"shared-photo-{number}"
        companion.add_shared_photo(file_id, photo.description, photo.note)
        shared_photo_descriptions[file_id] = photo.description
    transcript_lines = []
    for message in conversation.messages:
        transcript_lines.append(person_line(message))
        replies = send_and_collect_replies(
            companion, message, shared_photo_descriptions
        )
        transcript_lines += [f"Zeph: {reply}" for reply in replies]

    verdicts = judge_persona_rules(
        companion.judge_chat_model, "\n".join(transcript_lines), conversation.rules
    )

    if conversation.shared_photos and SEND_PHOTO_TOOL not in companion.offered_tools():
        raise EvalSetupError(
            "The send_photo tool was never offered, so this case tested nothing"
        )
    passed = all(verdict.passed for verdict in verdicts)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=[verdict_check(verdict) for verdict in verdicts],
        notes=[] if passed else transcript_lines,
    )
