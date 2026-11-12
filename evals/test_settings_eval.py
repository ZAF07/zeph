import pytest
from fastapi.testclient import TestClient

from evals.cases import CASES_DIR, SettingsCase, load_settings_cases
from evals.report import EvalReport, SettingsResult
from evals.token_counting_chat_model import TokenCountingChatModel
from tests.fakes import FakeAuthVerifier, FakeChatChannel
from tests.telegram_helpers import send_to_webhook, telegram_text_update
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_settings_via_chat import SETTINGS_TOOLS

pytestmark = pytest.mark.eval

SETTINGS_CASES = load_settings_cases(CASES_DIR / "settings.yaml")


@pytest.mark.parametrize(
    "case", SETTINGS_CASES, ids=[case.id for case in SETTINGS_CASES]
)
def test_settings_requests_call_the_right_tool(
    case: SettingsCase,
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    eval_report: EvalReport,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    chat_model.called_tools.clear()

    assert send_to_webhook(client, telegram_text_update(case.message)) == 200

    called = [name for name in chat_model.called_tools if name in SETTINGS_TOOLS]
    result = SettingsResult(case, called)
    eval_report.settings.append(result)
    replies = [sent.text for sent in chat_channel.sent]
    assert result.passed, "\n".join([result.describe(), *replies])
