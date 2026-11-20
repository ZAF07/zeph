import importlib
from datetime import timedelta
from types import ModuleType
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
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
    end_with_pattern_answer,
    pattern_keeping_answer,
    start_goes_quiet_pattern,
)
from tests.test_post_conversation import processing_answer, quiet_gap

NAMES_MUM = "mum is staying with me again next week"
CLOSE_TO_GOES_QUIET = "when something grabs me everything else goes quiet"
OFFERED_HERE = "offered to them in this Conversation"


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


def end_current_conversation(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> str:
    """Let the quiet gap pass and run the Conversation end; return what the
    Pattern keeping call was given."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked.", mood="fine"))
    chat_model.script_pattern_keeping(pattern_keeping_answer([]))
    scheduler.tick()
    return chat_model.pattern_keeping_calls[-1].history[0].text


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
    assert f"[1] (suspected) {GOES_QUIET}" in seen
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
    assert f"[1] (suspected) {GOES_QUIET}" in seen


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

    assert f"[1] (suspected) {GOES_QUIET}" in seen_later


def test_a_closed_pattern_never_reaches_the_reply_plan(
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
    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "pushed_back", "state": "closed"},
    )
    clock.advance(timedelta(days=365))

    seen = reply_plan_sees(client, chat_model, NAMES_MUM)

    assert "Mum's visit" in seen
    assert GOES_QUIET not in seen


def test_a_pushed_back_pattern_waits_the_admin_set_days_before_it_comes_back(
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
    set_settings(client, auth_verifier, {"pattern_pushed_back_wait_days": 10})
    end_with_pattern_answer(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        {"pattern": 1, "reaction": "pushed_back"},
    )

    clock.advance(timedelta(days=9))
    seen_while_waiting = reply_plan_sees(client, chat_model, NAMES_MUM)
    clock.advance(timedelta(days=2))
    seen_after = reply_plan_sees(client, chat_model, NAMES_MUM)

    assert GOES_QUIET not in seen_while_waiting
    assert GOES_QUIET in seen_after


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

    instructions = offer_goes_quiet(client, chat_model)

    assert GOES_QUIET in instructions
    assert "here's what I notice" in instructions
    assert "never as fact" in instructions


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
    chat_model.script_reply_plan(
        reply_plan_answer(
            read="It's the same pull again.", say_read=False, offer_pattern=1
        )
    )

    instructions = reply_instructions(client, chat_model, NAMES_MUM)
    keeping_sees = end_current_conversation(
        chat_model, clock, scheduler, seeded_settings
    )

    assert GOES_QUIET not in instructions
    assert OFFERED_HERE not in keeping_sees


def test_the_next_conversation_ends_keeping_call_sees_the_pattern_was_offered(
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

    offer_goes_quiet(client, chat_model)
    keeping_sees = end_current_conversation(
        chat_model, clock, scheduler, seeded_settings
    )

    assert f"[1] (suspected; {OFFERED_HERE}: judge how they took it" in keeping_sees
    assert GOES_QUIET in keeping_sees


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


def test_the_push_back_wait_is_admin_editable_with_a_hint(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.patch(
        "/api/admin/settings",
        json={"values": {"pattern_pushed_back_wait_days": 45}},
        headers=headers,
    )

    assert response.status_code == 200
    setting = response.json()["settings"]["pattern_pushed_back_wait_days"]
    assert setting["value"] == 45
    assert (
        setting["hint"]
        == EDITABLE_SETTINGS_BY_KEY["pattern_pushed_back_wait_days"].hint
    )
    assert "pushed back" in setting["hint"]


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
