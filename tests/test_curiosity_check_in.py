import json
from datetime import timedelta
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_check_in_kinds,
)
from companion.core.ports import MessageRefusedError
from tests.conftest import CHECK_IN_KINDS_SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    auth_headers,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_admin_check_ins import add_kind, list_kinds
from tests.test_check_in_sending import (
    ONE_DAY,
    recent_check_ins,
    send_answer,
    set_up_user_with_check_ins,
)
from tests.test_curiosities import (
    PRESENTATION,
    PRESENTATION_WHY,
    end_conversation,
    end_current_conversation,
    new_curiosity,
    stored_curiosities,
)
from tests.test_features import switch_for_everyone
from tests.test_older_summaries import set_settings

WONDERING = "Something I've been wondering"
WONDERING_OFFERED = f"- {WONDERING}: "
WEDDING = "How is the wedding planning going?"
WEDDING_WHY = "Their sister's wedding is in December and they are helping."


def wondering_answer(message: str, curiosity: Any) -> str:
    """Build the Check-in model's JSON answer for a "wondering" send.

    Args:
        message: The Check-in message.
        curiosity: The Curiosity's number, as the model names it.

    Returns:
        The JSON answer.
    """
    return json.dumps(
        {
            "decision": "send",
            "kind": WONDERING,
            "message": message,
            "curiosity": curiosity,
        }
    )


def set_up_user_with_due_curiosities(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    curiosities: list[dict[str, Any]] | None = None,
    **overrides: Any,
) -> dict[str, str]:
    """Set up a User with Check-ins on, keep Curiosities, and move to their day.

    A Conversation on Wednesday 11 Nov keeps the Curiosities (by default the
    presentation one, due Friday 13 Nov). The clock then moves on two days,
    to Friday 17:31 in Singapore, when the User's first Check-in is due.

    Args:
        client: The backend's test client.
        auth_verifier: The fake auth verifier.
        chat_channel: The fake chat channel.
        chat_model: The scripted chat model.
        clock: The fake clock.
        scheduler: The fake scheduler.
        seeded_settings: The seeded platform settings.
        curiosities: The Curiosities the keeping model writes.
        **overrides: Onboarding answers to change.

    Returns:
        The User's Dashboard API headers.
    """
    headers = set_up_user_with_check_ins(
        client, auth_verifier, chat_channel, **overrides
    )
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "big presentation to the board on Thursday, so nervous",
        curiosities if curiosities is not None else [new_curiosity()],
    )
    clock.advance(timedelta(days=2))
    chat_channel.sent.clear()
    return headers


def check_in_model_saw(chat_model: ScriptedChatModel) -> str:
    """Return what the latest Check-in model call was given."""
    [line] = chat_model.calls[-1].history
    return line.text


def test_a_due_user_with_a_due_curiosity_gets_a_check_in_that_asks_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    headers = set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script(wondering_answer("so... how did the presentation go?", 1))

    scheduler.tick()

    assert [sent.text for sent in chat_channel.sent] == [
        "so... how did the presentation go?"
    ]
    saw = check_in_model_saw(chat_model)
    assert WONDERING_OFFERED in saw
    assert f"1. {PRESENTATION} Why: {PRESENTATION_WHY} Sensitivity: low." in saw
    assert '"curiosity"' in saw
    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "raised"
    assert curiosity["raised_at"] == clock.now()
    assert curiosity["raised_conversation_id"] is None
    assert recent_check_ins(client, headers)[0]["kind"] == WONDERING
    log = client.get(
        "/api/admin/check-ins",
        params={"days": 7},
        headers=owner_headers(client, auth_verifier),
    ).json()["entries"]
    assert [(entry["outcome"], entry["kind"]) for entry in log] == [("sent", WONDERING)]


def test_a_reply_starts_a_conversation_the_curiosity_was_raised_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(), new_curiosity(ask=WEDDING, why=WEDDING_WHY)],
    )
    chat_model.script(wondering_answer("so... how did the presentation go?", 1))
    scheduler.tick()

    clock.advance(timedelta(hours=1))
    chat_model.script("that's brilliant, well done!")
    send_to_webhook(client, telegram_text_update("it went great!"))

    reply_call = chat_model.calls[-1]
    assert [line.text for line in reply_call.history] == [
        "so... how did the presentation go?",
        "it went great!",
    ]
    understanding_saw = chat_model.understanding_calls[-1].history[0].text
    assert "(raised 1 of at most 1 in this Conversation):\nNone." in understanding_saw
    assert WEDDING not in understanding_saw
    presentation, _ = stored_curiosities(engine)
    assert presentation["raised_conversation_id"] is not None

    end_current_conversation(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [{"curiosity": 1, "reaction": "engaged"}],
    )

    keeper_saw = chat_model.curiosity_keeping_calls[-1].history[0].text
    assert f"[1] (brought up in this Conversation) {PRESENTATION}" in keeper_saw
    presentation, wedding = stored_curiosities(engine)
    assert presentation["reaction"] == "engaged"
    assert wedding["state"] == "waiting"


def test_the_kind_is_not_offered_before_a_curiosity_is_due(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(not_before="2026-11-14")],
    )
    chat_model.script(send_answer("hey Maya, happy friday!"))

    scheduler.tick()

    saw = check_in_model_saw(chat_model)
    assert WONDERING_OFFERED not in saw
    assert PRESENTATION not in saw
    assert [sent.text for sent in chat_channel.sent] == ["hey Maya, happy friday!"]


def test_a_curiosity_is_due_on_its_day_in_the_users_time_zone(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(not_before="2026-11-14")],
        quiet_hours_start="03:00",
        quiet_hours_end="04:00",
    )
    clock.advance(timedelta(hours=7))
    chat_model.script(wondering_answer("so... how did the presentation go?", 1))

    scheduler.tick()

    assert clock.now().day == 13
    saw = check_in_model_saw(chat_model)
    assert WONDERING_OFFERED in saw
    assert f"1. {PRESENTATION}" in saw


def test_the_kind_is_not_offered_with_curiosities_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    switch_for_everyone(
        client, owner_headers(client, auth_verifier), "curiosities", False
    )
    chat_model.script(send_answer("hey Maya, happy friday!"))

    scheduler.tick()

    saw = check_in_model_saw(chat_model)
    assert WONDERING_OFFERED not in saw
    assert PRESENTATION not in saw
    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "waiting"


def test_no_more_than_the_weekly_limit_of_curiosity_check_ins_are_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(), new_curiosity(ask=WEDDING, why=WEDDING_WHY)],
    )
    chat_model.script(wondering_answer("how did the presentation go?", 1))
    scheduler.tick()

    clock.advance(ONE_DAY)
    chat_model.script(send_answer("hey Maya, how's your saturday?"))
    scheduler.tick()
    assert WONDERING_OFFERED not in check_in_model_saw(chat_model)

    clock.advance(timedelta(days=6, minutes=1))
    chat_model.script(wondering_answer("how's the wedding planning?", 1))
    scheduler.tick()
    saw = check_in_model_saw(chat_model)
    assert WONDERING_OFFERED in saw
    assert f"1. {WEDDING} Why: {WEDDING_WHY}" in saw
    assert PRESENTATION not in saw
    assert chat_channel.sent[-1].text == "how's the wedding planning?"


def test_the_weekly_limit_is_an_admin_setting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    assert seeded_settings["curiosity_check_ins_per_week"] == 1
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        [new_curiosity(), new_curiosity(ask=WEDDING, why=WEDDING_WHY)],
    )
    set_settings(client, auth_verifier, {"curiosity_check_ins_per_week": 2})
    chat_model.script(wondering_answer("how did the presentation go?", 1))
    scheduler.tick()

    clock.advance(ONE_DAY)
    chat_model.script(wondering_answer("how's the wedding planning?", 1))
    scheduler.tick()
    assert WONDERING_OFFERED in check_in_model_saw(chat_model)

    set_settings(client, auth_verifier, {"curiosity_check_ins_per_week": 0})
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "off to the beach",
        [new_curiosity(ask="How was the beach?", not_before=None)],
    )
    clock.advance(ONE_DAY)
    chat_model.script(send_answer("hey Maya"))
    scheduler.tick()
    assert WONDERING_OFFERED not in check_in_model_saw(chat_model)


def test_an_answer_naming_no_due_curiosity_sends_nothing_and_is_tried_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script(
        wondering_answer("how did it go?", 2),
        wondering_answer("how did it go?", None),
        wondering_answer("how did it go?", True),
        wondering_answer("how did it go?", 1),
    )

    for _ in range(4):
        scheduler.tick()
        clock.advance(timedelta(minutes=1))

    assert [sent.text for sent in chat_channel.sent] == ["how did it go?"]
    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "raised"


def test_a_refused_check_in_leaves_its_curiosity_waiting(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_channel.text_send_failures = [MessageRefusedError("Too Many Requests")]
    chat_model.script(wondering_answer("how did the presentation go?", 1))

    scheduler.tick()

    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "waiting"
    assert curiosity["raised_at"] is None


def test_a_check_in_that_may_have_arrived_marks_its_curiosity_raised(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    set_up_user_with_due_curiosities(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_channel.text_send_failures = [TimeoutError("Telegram took too long")]
    chat_model.script(wondering_answer("how did the presentation go?", 1))

    scheduler.tick()

    [curiosity] = stored_curiosities(engine)
    assert curiosity["state"] == "raised"


def test_admin_sees_the_kind_and_can_edit_its_wording_but_not_what_it_does(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    assert [kind["raises_curiosity"] for kind in list_kinds(client, admin)] == [
        False,
        False,
        False,
        False,
        False,
        True,
    ]
    [wondering] = [
        kind for kind in list_kinds(client, admin) if kind["raises_curiosity"]
    ]
    assert wondering["name"] == WONDERING

    edited = client.put(
        f"/api/admin/check-in-kinds/{wondering['id']}",
        json={
            "name": "A question I saved",
            "description": "Something you mentioned, asked when the time is right.",
            "raises_curiosity": False,
        },
        headers=admin,
    )

    assert edited.status_code == 200, edited.text
    assert edited.json()["name"] == "A question I saved"
    assert edited.json()["raises_curiosity"] is True
    assert add_kind(client, admin)["raises_curiosity"] is False


def test_users_see_the_kind_on_their_check_ins_page(
    client: TestClient, auth_verifier: FakeAuthVerifier, chat_channel: FakeChatChannel
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    maya = auth_headers(auth_verifier, "user_maya")

    kinds = client.get("/api/check-ins", headers=maya).json()["kinds"]

    assert kinds[-1]["name"] == WONDERING


def stored_kinds(engine: Engine) -> list[tuple[str, bool, int]]:
    """Read every Check-in Kind's name, Curiosity flag and place from the database.

    Args:
        engine: The database engine.

    Returns:
        Each Kind's name, whether it asks a Curiosity and its sort order.
    """
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT name, raises_curiosity, sort_order FROM check_in_kinds "
                "ORDER BY sort_order"
            )
        ).all()
    return [(row.name, row.raises_curiosity, row.sort_order) for row in rows]


def downgrade_to_before_wondering(database_url: str) -> None:
    """Take the database back to before the "wondering" Kind.

    Args:
        database_url: The test database's URL.
    """
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0033")


def test_an_existing_install_gets_the_wondering_kind_last(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_wondering(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM check_in_kinds"))
            connection.execute(
                text(
                    "INSERT INTO check_in_kinds (id, name, description, "
                    "sort_order, sends_shared_photo) VALUES "
                    "(gen_random_uuid(), 'A hello', 'Hi.', 0, false), "
                    "(gen_random_uuid(), 'A nudge', 'Go on.', 3, false)"
                )
            )
    finally:
        migrate(database_url)

    assert stored_kinds(engine) == [
        ("A hello", False, 0),
        ("A nudge", False, 3),
        (WONDERING, True, 4),
    ]


def test_a_fresh_install_gets_the_wondering_kind_from_the_seed_file(
    engine: Engine, database_url: str
) -> None:
    downgrade_to_before_wondering(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM check_in_kinds"))
    finally:
        migrate(database_url)
    seed_check_in_kinds(engine, CHECK_IN_KINDS_SEED_FILE)

    assert [(name, flag) for name, flag, _ in stored_kinds(engine)][-1] == (
        WONDERING,
        True,
    )
    assert sum(flag for _, flag, _ in stored_kinds(engine)) == 1
