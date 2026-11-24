from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.core.curiosities import NO_REASON_GIVEN
from companion.core.reply_plan import ASKS_WHY_INSTEAD
from companion.core.response_composition import (
    GUIDANCE_HEADING,
    MEMORY_HEADING,
    OPTIONAL_EXTRAS_HEADING,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import (
    connect_telegram,
    owner_headers,
)
from tests.test_admin_needs import list_needs, need_named
from tests.test_curiosities import (
    PRESENTATION,
    end_conversation,
    new_curiosity,
    presentation_is_due,
    reply_instructions,
    reply_plan_sees,
    stored_curiosities,
)
from tests.test_features import maya_id
from tests.test_model_call_log import newest_call
from tests.test_moves_migration import downgrade_to
from tests.test_older_summaries import set_settings
from tests.test_understanding import saved_reply_plans

DESK = "Did the new desk arrive?"
RAISE_FIRST = [{"curiosity": 1, "how": "weave"}]


def set_treatment(
    client: TestClient, admin: dict[str, str], need_name: str, treatment: str
) -> None:
    """Save how a Need treats Curiosities, as an Admin on the Needs page."""
    need = need_named(client, admin, need_name)
    response = client.put(
        f"/api/admin/needs/{need['id']}",
        json={
            "name": need["name"],
            "when_it_fits": need["when_it_fits"],
            "how_to_reply": need["how_to_reply"],
            "ruled_out_move_ids": need["ruled_out_move_ids"],
            "curiosities": treatment,
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text


def reply_to(client: TestClient, chat_model: ScriptedChatModel, **plan: Any) -> str:
    """Answer one message with the given Reply Plan; return the reply's instructions."""
    chat_model.script_reply_plan(reply_plan_answer(**plan))
    return reply_instructions(client, chat_model, "hey you")


def test_each_starting_need_says_how_curiosities_are_treated(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    treatments = {
        need["name"]: need["curiosities"] for need in list_needs(client, admin)
    }

    assert treatments == {
        "Be heard": "never",
        "Think it through": "ask_by_default",
        "Advice": "only_if_it_fits",
        "Accountability": "ask_by_default",
        "Get it done": "never",
        "Ask more": "only_if_it_fits",
        "Just chatting": "only_if_it_fits",
    }


def test_an_admin_saves_a_needs_curiosities_field_and_the_next_reply_plan_sees_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    admin = owner_headers(client, auth_verifier)
    before = reply_plan_sees(client, chat_model, "hey")

    set_treatment(client, admin, "Advice", "ask_by_default")

    after = reply_plan_sees(client, chat_model, "hey again")
    assert need_named(client, admin, "Advice")["curiosities"] == "ask_by_default"
    assert "How each Need treats them:" in before
    assert "- Advice: only if it fits the moment" in before
    assert "- Advice: ask by default: ask one in this reply, or say why not" in after
    assert "- Be heard: never: ask none" in after


def test_an_unknown_curiosities_choice_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)
    advice = need_named(client, admin, "Advice")

    response = client.put(
        f"/api/admin/needs/{advice['id']}",
        json={**advice, "curiosities": "always"},
        headers=admin,
    )

    assert response.status_code == 422
    assert need_named(client, admin, "Advice")["curiosities"] == "only_if_it_fits"


def test_under_ask_by_default_the_reason_for_not_asking_is_saved(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    reply_to(
        client,
        chat_model,
        need="Think it through",
        no_curiosity_why="They asked something that needs the whole reply.",
    )
    reply_to(client, chat_model, need="Think it through")
    reply_to(client, chat_model, need="Just chatting", no_curiosity_why="Not now.")

    reasons = [
        plan["form"]["curiosity_not_asked_why"] for plan in saved_reply_plans(engine)
    ]
    assert reasons[-3:] == [
        "They asked something that needs the whole reply.",
        NO_REASON_GIVEN,
        "",
    ]
    assert stored_curiosities(engine)[0]["state"] == "waiting"


def test_under_ask_by_default_an_asked_curiosity_saves_no_reason(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=RAISE_FIRST,
        no_curiosity_why="Odd: a reason with a pick.",
    )

    assert saved_reply_plans(engine)[-1]["form"]["curiosity_not_asked_why"] == ""
    assert stored_curiosities(engine)[0]["state"] == "raised"


def test_a_need_set_to_never_asks_no_curiosity_and_logs_none_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    instructions = reply_to(client, chat_model, need="Be heard", bring_up=RAISE_FIRST)

    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert PRESENTATION not in instructions
    assert saved_reply_plans(engine)[-1]["form"]["curiosities"] == []
    assert stored_curiosities(engine)[0]["state"] == "waiting"
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (0, False)


def test_a_picked_curiosity_is_part_of_the_plan_not_an_optional_extra(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)

    instructions = reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=RAISE_FIRST,
        memory_categories=["Goals"],
    )

    guidance_at = instructions.index(GUIDANCE_HEADING)
    asked_at = instructions.index(f"- {PRESENTATION}")
    later_headings = [
        instructions.find(heading)
        for heading in (MEMORY_HEADING, OPTIONAL_EXTRAS_HEADING)
        if heading in instructions
    ]
    shape = newest_call(client, owner_headers(client, auth_verifier), "reply_plan")[
        "reply_plan_shape"
    ]
    assert guidance_at < asked_at
    assert all(asked_at < heading_at for heading_at in later_headings)
    assert "It is part of the plan, not an extra to leave out" in instructions
    assert "something you've been wondering" not in instructions
    assert (shape["curiosities_offered"], shape["curiosity_asked"]) == (1, True)


def test_a_reply_asks_at_most_one_curiosity(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [new_curiosity(), new_curiosity(ask=DESK, not_before=None)],
    )
    clock.advance(timedelta(days=2))
    set_settings(client, auth_verifier, {"curiosities_per_conversation": 5})

    instructions = reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=[{"curiosity": 1, "how": "lead"}, {"curiosity": 2, "how": "weave"}],
    )

    states = [row["state"] for row in stored_curiosities(engine)]
    assert PRESENTATION in instructions
    assert DESK not in instructions
    assert states == ["raised", "waiting"]


def test_no_curiosity_is_offered_while_they_are_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_understanding(understanding_answer(struggling=True))
    chat_model.script_reply_plan(
        reply_plan_answer(need="Think it through", bring_up=RAISE_FIRST)
    )

    seen = reply_plan_sees(client, chat_model, "everything is falling apart")

    form = saved_reply_plans(engine)[-1]["form"]
    assert PRESENTATION not in seen
    assert (form["curiosities"], form["curiosity_not_asked_why"]) == ([], "")
    assert stored_curiosities(engine)[0]["state"] == "waiting"


def test_a_reply_that_asks_why_asks_no_curiosity_too(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    presentation_is_due(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_understanding(understanding_answer(cause_known=False))

    instructions = reply_to(
        client,
        chat_model,
        need="Think it through",
        bring_up=RAISE_FIRST,
        ask_why=True,
    )

    form = saved_reply_plans(engine)[-1]["form"]
    assert PRESENTATION not in instructions
    assert seeded_settings["reply_ask_why_note"].strip() in instructions
    assert (form["curiosities"], form["curiosity_not_asked_why"]) == (
        [],
        ASKS_WHY_INSTEAD,
    )


@pytest.mark.parametrize("aim", ["commitment", "look_back", "next_move"])
def test_a_new_curiosity_is_saved_with_its_aim(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
    aim: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [new_curiosity(aim=aim)],
    )

    assert [row["aim"] for row in stored_curiosities(engine)] == [aim]


def test_the_keeping_step_saves_no_curiosity_without_an_aim(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    engine: Engine,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    without_aim = new_curiosity(ask="No aim?")
    del without_aim["aim"]

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "work is a lot",
        [
            without_aim,
            new_curiosity(ask="Null aim?", aim=None),
            new_curiosity(ask="Odd aim?", aim="small talk"),
            new_curiosity(ask="A guess with no guess?", aim="guess"),
            {**new_curiosity(ask="Do you live near the sea?", aim=None), "guess": "x"},
            new_curiosity(ask=DESK, aim="look_back"),
        ],
    )

    saved = {row["question"]: row["aim"] for row in stored_curiosities(engine)}
    assert saved == {"Do you live near the sea?": "guess", DESK: "look_back"}


def test_the_curiosity_keeping_prompt_asks_for_an_aim_on_every_new_curiosity(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = " ".join(seeded_settings["curiosity_keeping_prompt"].split())

    assert "one without an aim is not saved" in prompt
    for aim in ("commitment", "look_back", "guess", "next_move"):
        assert f'"{aim}"' in prompt


def test_the_reply_plan_prompt_says_to_ask_one_or_say_why_not(
    seeded_settings: dict[str, Any],
) -> None:
    prompt = " ".join(seeded_settings["reply_plan_prompt"].split())

    assert "ask by default: pick one" in prompt
    assert "give that reason in no_curiosity_why" in prompt
    assert '"no_curiosity_why": "..." | null' in prompt


def test_the_migration_gives_saved_curiosities_an_aim_and_needs_their_treatment(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    engine: Engine,
    database_url: str,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = maya_id(client, auth_verifier)
    downgrade_to(database_url, "0079")
    try:
        with engine.begin() as connection:
            for question, guess, state in (
                ("Plain and waiting?", None, "waiting"),
                ("Guess and waiting?", "They live by the sea.", "waiting"),
                ("Plain and raised?", None, "raised"),
            ):
                connection.execute(
                    text(
                        "INSERT INTO curiosities (id, user_id, question, why, "
                        "sensitivity, state, created_at, guess, how_sure) VALUES "
                        "(:id, :user_id, :question, 'Why.', 'low', :state, now(), "
                        ":guess, :how_sure)"
                    ),
                    {
                        "id": uuid4(),
                        "user_id": user_id,
                        "question": question,
                        "state": state,
                        "guess": guess,
                        "how_sure": "low" if guess else None,
                    },
                )
            connection.execute(
                text(
                    "INSERT INTO needs (id, name, when_it_fits, how_to_reply, "
                    "sort_order) VALUES (:id, 'Celebrate', 'Good news.', "
                    "'Cheer.', 99)"
                ),
                {"id": uuid4()},
            )
            connection.execute(
                text("UPDATE needs SET name = 'BE HEARD' WHERE name = 'Be heard'")
            )
    finally:
        migrate(database_url)

    aims = {row["question"]: row["aim"] for row in stored_curiosities(engine)}
    with engine.begin() as connection:
        treatments = dict(
            connection.execute(text("SELECT name, curiosities FROM needs")).all()
        )
        connection.execute(text("DELETE FROM needs WHERE name = 'Celebrate'"))
        connection.execute(
            text("UPDATE needs SET name = 'Be heard' WHERE name = 'BE HEARD'")
        )
    assert aims == {
        "Plain and waiting?": "look_back",
        "Guess and waiting?": "guess",
        "Plain and raised?": "look_back",
    }
    assert treatments == {
        "BE HEARD": "never",
        "Think it through": "ask_by_default",
        "Advice": "only_if_it_fits",
        "Accountability": "ask_by_default",
        "Get it done": "never",
        "Ask more": "only_if_it_fits",
        "Just chatting": "only_if_it_fits",
        "Celebrate": "only_if_it_fits",
    }
