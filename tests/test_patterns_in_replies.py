import importlib
from datetime import timedelta
from types import ModuleType
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.core.models import PatternState
from companion.core.platform_settings import EDITABLE_SETTINGS_BY_KEY
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
)
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_life_threads import reply_instructions, reply_plan_sees
from tests.test_model_call_log import newest_call
from tests.test_moves_migration import downgrade_to
from tests.test_older_summaries import set_settings
from tests.test_patterns import (
    GOES_QUIET,
    set_pattern_state,
    start_goes_quiet_pattern,
)

NAMES_MUM = "mum is staying with me again next week"
CLOSE_TO_GOES_QUIET = "when something grabs me everything else goes quiet"


def have_goes_quiet_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Connect Maya and keep the suspected Pattern linking the side project
    and mum's visit, then let a few days pass."""
    connect_telegram(client, auth_verifier, chat_channel)
    start_goes_quiet_pattern(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=3))


def offer_goes_quiet(client: TestClient, chat_model: ScriptedChatModel) -> str:
    """Send a message naming mum whose Reply Plan says its Read and offers the
    Pattern; return what the reply call was told."""
    chat_model.script_reply_plan(
        reply_plan_answer(
            read="Whatever grabs them crowds out the people around them.",
            say_read=True,
            patterns_used=[1],
            offer_pattern=1,
        )
    )
    return reply_instructions(client, chat_model, NAMES_MUM)


def test_a_pattern_linked_to_a_reminded_thread_reaches_the_reply_plan(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    seen = reply_plan_sees(client, chat_model, NAMES_MUM)

    assert "Mum's visit" in seen
    assert f"[1] (unmatched) {GOES_QUIET}" in seen
    assert "Snapped at mum because the app had them." in seen


def test_a_pattern_close_in_meaning_to_a_message_with_no_thread_reaches_it_too(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    seen = reply_plan_sees(client, chat_model, CLOSE_TO_GOES_QUIET)

    assert "then those from earlier in this Conversation:\nNone." in seen
    assert f"[1] (unmatched) {GOES_QUIET}" in seen


def test_a_message_far_from_every_pattern_and_thread_brings_no_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    seen = reply_plan_sees(client, chat_model, "any good podcasts about space?")

    assert GOES_QUIET not in seen


def test_direct_pattern_recall_follows_the_pattern_bar_not_the_thread_bar(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_settings(
        client,
        auth_verifier,
        {"life_threads_closeness_percent": 100, "pattern_closeness_percent": 20},
    )
    loose = reply_plan_sees(client, chat_model, CLOSE_TO_GOES_QUIET)
    clock.advance(timedelta(days=1))
    set_settings(client, auth_verifier, {"pattern_closeness_percent": 100})
    strict = reply_plan_sees(client, chat_model, CLOSE_TO_GOES_QUIET)

    assert GOES_QUIET in loose
    assert GOES_QUIET not in strict


def test_a_pattern_in_mind_stays_in_mind_for_the_conversation(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_settings(client, auth_verifier, {"life_threads_texts_to_search": 1})

    reply_plan_sees(client, chat_model, CLOSE_TO_GOES_QUIET)
    seen_later = reply_plan_sees(client, chat_model, "any good podcasts about space?")

    assert f"[1] (unmatched) {GOES_QUIET}" in seen_later


def test_an_offered_pattern_reaches_the_reply_as_zephs_view(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_pattern_state(client.engine, PatternState.CONFIRMED)

    instructions = offer_goes_quiet(client, chat_model)

    assert GOES_QUIET in instructions
    assert "here's what I notice" in instructions
    assert "never as fact" in instructions


def test_an_unmatched_pattern_shapes_the_read_but_is_never_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    admin = owner_headers(client, auth_verifier)

    instructions = offer_goes_quiet(client, chat_model)

    seen = chat_model.reply_plan_calls[-1].history[0].text
    assert "never offer it or say it as a pattern" in seen
    assert "Whatever grabs them crowds out the people around them." in instructions
    assert GOES_QUIET not in instructions
    assert "here's what I notice" not in instructions
    shape = newest_call(client, admin, "reply_plan")["reply_plan_shape"]
    assert (shape["pattern_used"], shape["pattern_offered"]) == (True, False)


def test_a_pattern_used_but_not_offered_never_reaches_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_reply_plan(
        reply_plan_answer(read="It's the same pull again.", patterns_used=[1])
    )

    instructions = reply_instructions(client, chat_model, NAMES_MUM)

    assert GOES_QUIET not in instructions


def test_a_pattern_is_offered_only_when_the_read_is_said(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_pattern_state(client.engine, PatternState.CONFIRMED)
    chat_model.script_reply_plan(
        reply_plan_answer(
            read="It's the same pull again.", say_read=False, offer_pattern=1
        )
    )

    instructions = reply_instructions(client, chat_model, NAMES_MUM)

    assert GOES_QUIET not in instructions


def test_the_model_call_log_shows_whether_a_pattern_was_used_or_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    have_goes_quiet_pattern(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_pattern_state(client.engine, PatternState.CONFIRMED)
    admin = owner_headers(client, auth_verifier)

    def shape_after(answer: str) -> dict[str, Any]:
        """Send a message naming mum with this Reply Plan answer and return
        its Reply Plan shape from the Model Call Log."""
        chat_model.script_reply_plan(answer)
        chat_model.script("mm, tell me more")
        send_to_webhook(client, telegram_text_update(NAMES_MUM))
        shape: dict[str, Any] = newest_call(client, admin, "reply_plan")[
            "reply_plan_shape"
        ]
        return shape

    none = shape_after(reply_plan_answer())
    used = shape_after(reply_plan_answer(read="The pull.", patterns_used=[1]))
    offered = shape_after(
        reply_plan_answer(read="The pull.", say_read=True, offer_pattern=1)
    )

    assert (none["pattern_used"], none["pattern_offered"]) == (False, False)
    assert (used["pattern_used"], used["pattern_offered"]) == (True, False)
    assert (offered["pattern_used"], offered["pattern_offered"]) == (True, True)


def test_the_pattern_bar_is_admin_editable_with_a_hint_and_seeded_at_52(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    seeded_settings: dict[str, Any],
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"pattern_closeness_percent": 58}},
        headers=headers,
    )

    assert seeded_settings["pattern_closeness_percent"] == 52
    assert response.status_code == 200
    setting_key = "pattern_closeness_percent"
    thread_bar_key = "life_threads_closeness_percent"
    setting = response.json()["settings"][setting_key]
    assert setting["value"] == 58
    assert setting["hint"] == EDITABLE_SETTINGS_BY_KEY[setting_key].hint
    assert "Pattern" in setting["hint"]
    assert "Pattern" not in EDITABLE_SETTINGS_BY_KEY[thread_bar_key].hint


def patterns_in_replies_migration() -> ModuleType:
    """Load the Patterns in replies migration module."""
    return importlib.import_module(
        "companion.adapters.postgres.migrations.versions.0073_patterns_in_replies"
    )


def stored_reply_plan_prompt(engine: Engine) -> str | None:
    """Read the stored Reply Plan prompt, or None if it isn't stored."""
    with engine.connect() as connection:
        value: str | None = connection.execute(
            text(
                "SELECT value #>> '{}' FROM platform_settings "
                "WHERE key = 'reply_plan_prompt'"
            )
        ).scalar_one_or_none()
    return value


def test_the_migration_reloads_the_reply_plan_prompt_so_it_sees_patterns(
    engine: Engine, database_url: str
) -> None:
    downgrade_to(database_url, "0072")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE platform_settings SET value = to_jsonb(CAST(:p AS text)) "
                    "WHERE key = 'reply_plan_prompt'"
                ),
                {"p": "An old Reply Plan prompt with no Patterns."},
            )
    finally:
        migrate(database_url)

    assert patterns_in_replies_migration().revision == "0073"
    assert stored_reply_plan_prompt(engine) is None


def test_the_reply_plan_prompt_asks_which_pattern_is_used_and_offered(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = seeded_settings["reply_plan_prompt"]

    assert '"patterns_used"' in prompt
    assert '"offer_pattern"' in prompt
