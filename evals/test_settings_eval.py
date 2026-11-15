from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from evals.cases import CASES_DIR, SettingsCase, load_settings_cases
from evals.made_up_memory import save_memory_items
from evals.report import EvalReport, SettingsResult
from evals.token_counting_chat_model import TokenCountingChatModel
from tests.fakes import FakeAuthVerifier, FakeChatChannel, FakeClock
from tests.telegram_helpers import send_to_webhook, telegram_text_update
from tests.test_check_in_sending import set_up_user_with_check_ins
from tests.test_post_conversation import memory_contents
from tests.test_settings_via_chat import SETTINGS_TOOLS

pytestmark = pytest.mark.eval

SETTINGS_CASES = load_settings_cases(CASES_DIR / "settings.yaml")


@pytest.mark.parametrize(
    "case", SETTINGS_CASES, ids=[case.id for case in SETTINGS_CASES]
)
def test_settings_requests_call_the_right_tool(
    case: SettingsCase,
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: TokenCountingChatModel,
    clock: FakeClock,
    eval_report: EvalReport,
) -> None:
    no_onboarding_memory = (
        {"onboarding_reasons": [], "onboarding_note": None} if case.memories else {}
    )
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, **no_onboarding_memory
    )
    user_id = UUID(client.get("/api/me", headers=headers).json()["id"])
    save_memory_items(
        build_postgres_repositories(engine), user_id, case.memories, clock.now()
    )
    chat_model.called_tools.clear()

    assert send_to_webhook(client, telegram_text_update(case.message)) == 200

    called = [name for name in chat_model.called_tools if name in SETTINGS_TOOLS]
    memory_after = [
        content
        for contents in memory_contents(client, headers).values()
        for content in contents
    ]
    result = SettingsResult(case, called, memory_after)
    eval_report.settings.append(result)
    replies = [sent.text for sent in chat_channel.sent]
    assert result.passed, "\n".join([result.describe(), *replies])
