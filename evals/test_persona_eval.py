import pytest
from fastapi.testclient import TestClient

from evals.cases import (
    CASES_DIR,
    PersonaConversation,
    PersonaMessage,
    load_persona_cases,
)
from evals.judge import judge_persona_rules
from evals.report import EvalReport, PersonaResult, verdict_line
from evals.token_counting_chat_model import TokenCountingChatModel
from tests.fakes import FakeAuthVerifier, FakeChatChannel
from tests.telegram_helpers import (
    connect_telegram,
    send_to_webhook,
    telegram_message_update,
    telegram_text_update,
)

pytestmark = pytest.mark.eval

PERSONA_CASES = load_persona_cases(CASES_DIR / "persona.yaml")


def send_and_collect_replies(
    client: TestClient, chat_channel: FakeChatChannel, message: PersonaMessage
) -> list[str]:
    """Send one scripted message through the webhook and return Zeph's texts.

    Args:
        client: The backend's test client.
        chat_channel: Records what Zeph sends.
        message: The scripted message, text or a captioned photo.

    Returns:
        The texts Zeph sent in reply, in order.
    """
    if message.photo:
        update = telegram_message_update(
            {"photo": [{"file_id": "photo-1", "width": 800}], "caption": message.text}
        )
    else:
        update = telegram_text_update(message.text)
    already_sent = len(chat_channel.sent)
    assert send_to_webhook(client, update) == 200
    return [sent.text for sent in chat_channel.sent[already_sent:]]


def person_line(message: PersonaMessage) -> str:
    """Write the person's message as one line of the judge's transcript.

    Args:
        message: The scripted message.

    Returns:
        The line, e.g. "Person: hey".
    """
    if message.photo:
        return f"Person: (sends a photo with the caption) {message.text}"
    return f"Person: {message.text}"


@pytest.mark.parametrize(
    "conversation",
    PERSONA_CASES.conversations,
    ids=[conversation.id for conversation in PERSONA_CASES.conversations],
)
def test_replies_keep_the_persona_rules(
    conversation: PersonaConversation,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    eval_report: EvalReport,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    transcript_lines = []
    for message in conversation.messages:
        transcript_lines.append(person_line(message))
        replies = send_and_collect_replies(client, chat_channel, message)
        transcript_lines += [f"Zeph: {reply}" for reply in replies]
    transcript = "\n".join(transcript_lines)

    rules = {rule: PERSONA_CASES.rules[rule] for rule in conversation.rules}
    verdicts = judge_persona_rules(chat_model, transcript, rules)

    eval_report.persona.append(PersonaResult(conversation.id, verdicts))
    broken = [verdict_line(verdict) for verdict in verdicts if not verdict.passed]
    assert not broken, "\n".join([transcript, "", *broken])
