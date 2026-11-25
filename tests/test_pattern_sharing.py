import json
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import migrate
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.chat_settings import CONTESTED_GATHERING_TOOL
from companion.core.models import (
    PatternReaction,
    PatternState,
    Prediction,
    ReactionToPattern,
    RiskType,
    SafeguardEvent,
)
from companion.core.pattern_sharing import SHARED_CHECK_PROMPT
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    ToolCall,
    reply_plan_answer,
    understanding_answer,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_admin_check_ins import list_kinds
from tests.test_check_in_sending import send_answer, set_up_user_with_check_ins
from tests.test_curiosity_check_in import check_in_model_saw
from tests.test_explorations import talk, turn_exploring_on
from tests.test_features import switch_for_user, user_features_by_key
from tests.test_life_threads import thread_keeping_answer
from tests.test_model_call_log import newest_call
from tests.test_moves_migration import downgrade_to
from tests.test_pattern_states import BELONG, moves_of, states_and_causes
from tests.test_pattern_tagging import observation_entry, observations_of
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_ready_gate import belonging, make_belonging_ready, suspect_belonging
from tests.test_recent_messages import change_settings
from tests.test_settings_via_chat import me, reply_call

OFFER_HEADER = "A Pattern you may tell them now"
CONTESTED_HEADER = "Patterns you told them that they disagreed with"
TOLD_HEADER = "Patterns Zeph has told them:"
APPROVED_WORDING = "You seem to protect closeness by keeping disagreements small"
PREDICTION_WORDING = "notice whether you say yes before you've decided"
NOTICED_KIND = "Something I've noticed"
SHARING_SETTINGS = ("patterns_shared_per_week", "pattern_share_wait_days")
PREDICTION = "Next time Mei asks for something, notice whether you say yes first."
SHARED = json.dumps({"shared": True, "prediction": PREDICTION})
NOT_SHARED = json.dumps({"shared": False, "prediction": ""})
SHARING_REPLY = (
    "Can I tell you something I've noticed? When someone matters to you, you "
    "tend to say yes and swallow the rest. You said “I said yes to Mei again”, "
    "and “I just went along with it” with Jun. Next time Mei asks for something, "
    "notice whether you say yes first. What would prove me wrong?"
)


def turn_sharing_on(client: TestClient, auth_verifier: FakeAuthVerifier) -> str:
    """Turn Pattern noticing, exploring and sharing on for Maya only."""
    user_id = turn_exploring_on(client, auth_verifier)
    switch_for_user(
        client, owner_headers(client, auth_verifier), user_id, "pattern_sharing", "on"
    )
    return user_id


def predictions_of(engine: Engine, user_id: str) -> list[Prediction]:
    """List the Predictions given to a User through their repository."""
    return build_postgres_repositories(engine).patterns.list_predictions(UUID(user_id))


def reactions_of(engine: Engine, user_id: str) -> list[ReactionToPattern]:
    """List how a User took their Patterns through their repository."""
    return build_postgres_repositories(engine).patterns.list_reactions(UUID(user_id))


def share(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    check: str = SHARED,
    message: str = "I've been thinking about why I do that",
) -> str:
    """Have a reply share the ready Pattern; return what the reply was told."""
    clock.advance(timedelta(minutes=1))
    chat_model.script_reply_plan(reply_plan_answer(share_pattern=True))
    chat_model.script_shared_check(check)
    chat_model.script(SHARING_REPLY)
    send_to_webhook(client, telegram_text_update(message))
    return chat_model.calls[-1].instructions


def end_with(
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    reactions: list[dict[str, Any]] | None = None,
    observations: list[dict[str, Any]] | None = None,
) -> str:
    """End the open Conversation, tagged as given; return what tagging was given."""
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer(summary="Talked about Mei."))
    chat_model.script_thread_keeping(thread_keeping_answer([]))
    chat_model.script_pattern_tagging(
        json.dumps({"observations": observations or [], "reactions": reactions or []})
    )
    scheduler.tick()
    return chat_model.pattern_tagging_calls[-1].history[0].text


def ready_to_share(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> str:
    """Give Maya Pattern sharing and a ready Pattern of CONF.AVOID.BELONG."""
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_sharing_on(client, auth_verifier)
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    assert belonging(client.engine, user_id).state == PatternState.READY
    return user_id


def test_a_ready_pattern_is_offered_to_the_reply_plan_with_quotes_from_many_threads(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    saw = talk(client, chat_model, clock, "hey, slow evening here")

    offered = saw[saw.index(OFFER_HEADER) :].split("\n\n")[0]
    assert APPROVED_WORDING in offered
    assert "It shows with family, friend; not with partner." in offered
    assert "“I said yes to Mei again”" in offered
    assert "“Then I stewed on it all night”" in offered
    assert "“I just went along with it”" in offered
    assert "With Sam I say what I think" not in offered
    assert BELONG not in offered


def test_a_pattern_that_is_not_ready_is_never_offered_and_never_reaches_the_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    user_id = turn_sharing_on(client, auth_verifier)
    suspect_belonging(client, chat_model, clock, scheduler, seeded_settings)
    assert belonging(client.engine, user_id).state == PatternState.SUSPECTED

    saw = talk(client, chat_model, clock, "hey, slow evening here", share_pattern=True)

    assert OFFER_HEADER not in saw
    assert "never name them" in saw
    assert APPROVED_WORDING not in chat_model.calls[-1].instructions
    assert chat_model.shared_check_calls == []
    assert belonging(client.engine, user_id).state == PatternState.SUSPECTED


def test_the_reply_is_told_the_three_parts_as_zephs_view_with_no_clinical_words(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    told = share(client, chat_model, clock)

    section = told[told.index("Tell them this Pattern in this reply") :]
    assert "It is part of the plan, not an extra to leave out" in section
    assert "your view of them, never a fact" in section
    assert "no clinical or diagnostic words" in section
    assert "1. The Pattern, in your own warm words" in section
    assert APPROVED_WORDING in section
    assert "It shows with family, friend; not with partner." in section
    assert "quote two or three of these word for word" in section
    assert "“I said yes to Mei again”" in section
    assert "“I just went along with it”" in section
    assert "3. One Prediction" in section
    assert PREDICTION_WORDING in section
    assert "ask them what would prove it wrong" in section
    assert BELONG not in told
    assert "Softening disagreement to protect belonging" not in told


def test_only_when_the_check_says_so_is_it_shared_with_its_prediction_and_logged(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    share(client, chat_model, clock, check=NOT_SHARED)

    assert belonging(client.engine, user_id).state == PatternState.READY
    assert predictions_of(client.engine, user_id) == []
    [check] = chat_model.shared_check_calls
    assert check.instructions == SHARED_CHECK_PROMPT
    assert check.model == seeded_settings["check_in_model"]
    assert check.thinking is False
    assert SHARING_REPLY in check.history[0].text
    assert APPROVED_WORDING in check.history[0].text
    assert chat_model.call_order.index("shared_check") > chat_model.call_order.index(
        "reply"
    )

    share(client, chat_model, clock, check=SHARED)

    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SHARED
    assert pattern.shared_at == clock.now()
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("ready", "shared", "shared_in_chat")]
    assert move.conversation_id is not None
    [prediction] = predictions_of(client.engine, user_id)
    assert (prediction.pattern_id, prediction.wording) == (pattern.id, PREDICTION)


def test_a_failed_or_unreadable_check_leaves_it_ready_and_the_reply_still_goes(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_channel.sent.clear()

    share(client, chat_model, clock, check="it did, I think")
    chat_model.script_shared_check(RuntimeError("model down"))
    share(client, chat_model, clock, check=NOT_SHARED)

    assert belonging(client.engine, user_id).state == PatternState.READY
    assert [sent.text for sent in chat_channel.sent].count(SHARING_REPLY) == 2


def test_no_more_than_the_admin_set_number_are_shared_in_a_week(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    with client.engine.begin() as connection:
        connection.execute(text("UPDATE patterns SET state = 'ready'"))

    assert OFFER_HEADER not in talk(client, chat_model, clock, "quiet night")

    change_settings(client, auth_verifier, {"patterns_shared_per_week": 2})

    assert OFFER_HEADER in talk(client, chat_model, clock, "still quiet")

    change_settings(client, auth_verifier, {"patterns_shared_per_week": 1})
    clock.advance(timedelta(days=7, minutes=5))

    assert OFFER_HEADER in talk(client, chat_model, clock, "a week on")
    assert belonging(client.engine, user_id).state == PatternState.READY


def test_it_is_never_offered_while_the_user_is_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    chat_model.script_understanding(understanding_answer(struggling=True))

    saw = talk(client, chat_model, clock, "I can't cope today", share_pattern=True)

    assert OFFER_HEADER not in saw
    assert APPROVED_WORDING not in chat_model.calls[-1].instructions
    assert chat_model.shared_check_calls == []
    assert belonging(client.engine, user_id).state == PatternState.READY


def test_a_ready_pattern_is_looked_at_again_before_it_is_offered(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    build_postgres_repositories(client.engine).safeguard_events.add(
        SafeguardEvent(
            id=uuid4(),
            user_id=UUID(user_id),
            risk_type=RiskType.SUICIDE_OR_SELF_HARM,
            created_at=clock.now(),
            helplines_country=None,
        )
    )

    saw = talk(client, chat_model, clock, "hey", share_pattern=True)

    assert OFFER_HEADER not in saw
    assert belonging(client.engine, user_id).state == PatternState.SUSPECTED
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [
        ("ready", "suspected", "looked_before_sharing")
    ]
    assert chat_model.other_side_calls[1:] == []


def test_a_reply_that_shares_a_pattern_asks_no_curiosity_and_does_not_ask_why(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    clock.advance(timedelta(minutes=1))
    chat_model.script_reply_plan(
        reply_plan_answer(
            need="Think it through",
            share_pattern=True,
            ask_why=True,
            bring_up=[{"curiosity": 1, "how": "lead"}],
        )
    )
    chat_model.script_understanding(understanding_answer(cause_known=False))
    chat_model.script_shared_check(SHARED)
    chat_model.script(SHARING_REPLY)

    send_to_webhook(client, telegram_text_update("I keep doing this"))

    told = chat_model.calls[-1].instructions
    assert "Tell them this Pattern in this reply" in told
    assert seeded_settings["reply_ask_why_note"] not in told
    assert "Ask them this in this reply" not in told


def test_the_reply_plan_shape_records_whether_a_pattern_was_offered_and_shared(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    admin = owner_headers(client, auth_verifier)

    def shape() -> dict[str, Any]:
        """The newest Reply Plan's shape, with only its sharing fields."""
        whole = newest_call(client, admin, "reply_plan")["reply_plan_shape"]
        return {
            key: whole[key]
            for key in (
                "pattern_to_share_offered",
                "pattern_share_planned",
                "pattern_shared",
            )
        }

    talk(client, chat_model, clock, "slow evening")
    assert shape() == {
        "pattern_to_share_offered": True,
        "pattern_share_planned": False,
        "pattern_shared": None,
    }

    share(client, chat_model, clock, check=NOT_SHARED)
    assert shape() == {
        "pattern_to_share_offered": True,
        "pattern_share_planned": True,
        "pattern_shared": False,
    }

    share(client, chat_model, clock, check=SHARED)
    assert shape() == {
        "pattern_to_share_offered": True,
        "pattern_share_planned": True,
        "pattern_shared": True,
    }
    assert newest_call(client, admin, "pattern_shared_check")["content"] is None

    talk(client, chat_model, clock, "thanks for that")
    assert shape() == {
        "pattern_to_share_offered": False,
        "pattern_share_planned": False,
        "pattern_shared": None,
    }


def test_with_pattern_sharing_off_nothing_is_shared_and_a_ready_pattern_waits(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    admin = owner_headers(client, auth_verifier)
    switch_for_user(client, admin, user_id, "pattern_sharing", "off")

    saw = talk(client, chat_model, clock, "slow evening", share_pattern=True)

    assert OFFER_HEADER not in saw
    assert APPROVED_WORDING not in chat_model.calls[-1].instructions
    assert chat_model.shared_check_calls == []
    assert belonging(client.engine, user_id).state == PatternState.READY

    switch_for_user(client, admin, user_id, "pattern_sharing", "on")

    assert OFFER_HEADER in talk(client, chat_model, clock, "still slow")


def test_pattern_sharing_is_off_to_start_and_works_only_while_exploring_works(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    user_id = turn_sharing_on(client, auth_verifier)
    admin = owner_headers(client, auth_verifier)
    everyone = client.get("/api/admin/features", headers=admin).json()["features"]
    [sharing_for_everyone] = [
        feature for feature in everyone if feature["feature"] == "pattern_sharing"
    ]
    assert sharing_for_everyone["on"] is False
    assert user_features_by_key(client, admin, user_id)["pattern_sharing"]["works"]

    switch_for_user(client, admin, user_id, "pattern_exploring", "off")

    sharing = user_features_by_key(client, admin, user_id)["pattern_sharing"]
    assert (sharing["works"], sharing["reason"]) == (False, "pattern_exploring_off")

    switch_for_user(client, admin, user_id, "pattern_exploring", "on")
    switch_for_user(client, admin, user_id, "pattern_noticing", "off")

    sharing = user_features_by_key(client, admin, user_id)["pattern_sharing"]
    assert (sharing["works"], sharing["reason"]) == (False, "pattern_exploring_off")


def test_a_ready_pattern_not_shared_within_the_admin_set_days_goes_out_as_a_check_in(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = turn_sharing_on(client, auth_verifier)
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    assert belonging(client.engine, user_id).state == PatternState.READY

    clock.advance(timedelta(days=1, hours=10))
    chat_model.script(send_answer("hey, how's the week going?"))
    scheduler.tick()

    assert f"- {NOTICED_KIND}:" not in check_in_model_saw(chat_model)
    assert belonging(client.engine, user_id).state == PatternState.READY

    clock.advance(timedelta(days=5))
    chat_model.script(send_answer(SHARING_REPLY, NOTICED_KIND))
    chat_model.script_shared_check(SHARED)
    chat_channel.sent.clear()
    scheduler.tick()

    saw = check_in_model_saw(chat_model)
    assert f"- {NOTICED_KIND}:" in saw
    assert "- A casual hello:" not in saw
    assert APPROVED_WORDING in saw
    assert "“I said yes to Mei again”" in saw
    assert PREDICTION_WORDING in saw
    assert "ask them what would prove it wrong" in saw
    assert [sent.text for sent in chat_channel.sent] == [SHARING_REPLY]
    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SHARED
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("ready", "shared", "shared_in_check_in")]
    assert move.conversation_id is None
    assert [item.wording for item in predictions_of(client.engine, user_id)] == [
        PREDICTION
    ]


def test_a_check_in_never_shares_one_after_a_message_read_as_struggling(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    user_id = turn_sharing_on(client, auth_verifier)
    make_belonging_ready(client, chat_model, clock, scheduler, seeded_settings)
    chat_model.script_understanding(understanding_answer(struggling=True))
    talk(client, chat_model, clock, "everything is too much")
    end_with(chat_model, clock, scheduler, seeded_settings)

    clock.advance(timedelta(days=6, hours=10))
    chat_model.script(send_answer("thinking of you"))
    scheduler.tick()

    saw = check_in_model_saw(chat_model)
    assert f"- {NOTICED_KIND}:" not in saw
    assert "- A casual hello:" in saw
    assert belonging(client.engine, user_id).state == PatternState.READY


def test_agreeing_adds_a_weak_sign_for_and_never_confirms_by_itself(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    talk(client, chat_model, clock, "huh. yes, that's exactly what I do with Mei")

    tagging_saw = end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "agreed"}],
    )

    told = tagging_saw[tagging_saw.index(TOLD_HEADER) :].split("\n\n")[0]
    assert f"[1] {APPROVED_WORDING}" in told
    pattern = belonging(client.engine, user_id)
    assert pattern.state == PatternState.SHARED
    [reaction] = reactions_of(client.engine, user_id)
    assert (reaction.pattern_id, reaction.reaction) == (
        pattern.id,
        PatternReaction.AGREED,
    )

    talk(client, chat_model, clock, "it really is true, I did it again today")
    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "agreed"}],
    )

    assert len(reactions_of(client.engine, user_id)) == 2
    assert belonging(client.engine, user_id).state == PatternState.SHARED


def test_rejecting_makes_it_contested_and_it_is_never_offered_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    change_settings(client, auth_verifier, {"patterns_shared_per_week": 7})
    share(client, chat_model, clock)
    talk(client, chat_model, clock, "no, that's not me at all")

    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "pushed_back"}],
    )

    assert belonging(client.engine, user_id).state == PatternState.CONTESTED
    move = moves_of(client.engine, user_id)[-1]
    assert states_and_causes([move]) == [("shared", "contested", "user_reacted")]
    assert move.conversation_id is not None

    saw = talk(client, chat_model, clock, "anyway, slow evening", share_pattern=True)

    assert OFFER_HEADER not in saw
    contested = saw[saw.index(CONTESTED_HEADER) :].split("\n\n")[0]
    assert "Never bring one up or hint at it" in contested
    assert f"[1] {APPROVED_WORDING}" in contested
    assert APPROVED_WORDING not in chat_model.calls[-1].instructions
    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        observations=[
            observation_entry(quote="anyway, slow evening", about="their mother")
        ],
    )
    assert belonging(client.engine, user_id).state == PatternState.CONTESTED


def test_a_contested_pattern_is_talked_about_only_when_the_user_raises_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    talk(client, chat_model, clock, "no, that's not me at all")
    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "pushed_back"}],
    )

    talk(
        client,
        chat_model,
        clock,
        "that thing you said about me saying yes... maybe",
        raised_pattern=1,
    )

    told = chat_model.calls[-1].instructions
    assert "have now brought it up themselves" in told
    assert APPROVED_WORDING in told
    assert "Don't press it" in told
    assert belonging(client.engine, user_id).state == PatternState.CONTESTED


def test_the_users_switch_stops_new_observations_for_a_contested_pattern(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    maya = auth_headers(auth_verifier, "user_maya")
    share(client, chat_model, clock)
    talk(client, chat_model, clock, "no, that's not me. I gave in to mum again though")
    gave_in = observation_entry(quote="I gave in to mum again", about="their mother")
    assert me(client, maya)["contested_gathering_enabled"] is True
    assert me(client, maya)["pattern_sharing_works"] is True

    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "pushed_back"}],
        observations=[gave_in],
    )

    kept = len(observations_of(client.engine, user_id))
    assert kept == 5

    response = client.patch(
        "/api/me", json={"contested_gathering_enabled": False}, headers=maya
    )
    assert response.status_code == 200
    assert response.json()["contested_gathering_enabled"] is False
    talk(client, chat_model, clock, "I gave in to mum again today")
    end_with(chat_model, clock, scheduler, seeded_settings, observations=[gave_in])

    assert len(observations_of(client.engine, user_id)) == kept
    tagging = newest_tagging_shape(client, owner_headers(client, auth_verifier))
    assert tagging == {"tagged": 1, "dropped": 1}

    client.patch("/api/me", json={"contested_gathering_enabled": True}, headers=maya)
    talk(client, chat_model, clock, "and I gave in to mum again, third time")
    end_with(chat_model, clock, scheduler, seeded_settings, observations=[gave_in])

    assert len(observations_of(client.engine, user_id)) == kept + 1


def newest_tagging_shape(client: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """The shape of the newest Pattern tagging call in the Model Call Log."""
    traces = client.get("/api/admin/model-calls", headers=admin).json()["traces"]
    for trace in traces:
        calls = client.get(
            f"/api/admin/model-calls/{trace['trace_id']}", headers=admin
        ).json()["calls"]
        for call in calls:
            if call["step"] == "pattern_tagging":
                shape: dict[str, Any] = call["tagging_shape"]
                return shape
    raise AssertionError("No Pattern tagging call in the Model Call Log")


def test_the_switch_is_changed_in_chat_only_while_pattern_sharing_works(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    chat_model.script("hello!")
    send_to_webhook(client, telegram_text_update("hi"))
    assert CONTESTED_GATHERING_TOOL not in {
        tool.name for tool in chat_model.calls[-1].tools
    }
    assert me(client, headers)["pattern_sharing_works"] is False

    turn_sharing_on(client, auth_verifier)
    call = reply_call(
        client,
        chat_model,
        "stop looking for that, it isn't me",
        ToolCall(CONTESTED_GATHERING_TOOL, {"on": False}),
        "Okay, I've stopped.",
    )

    assert "no longer note anything new" in call.tool_results[0]
    assert me(client, headers)["contested_gathering_enabled"] is False
    assert "contested_gathering" in me(client, headers)["changed_in_chat"]

    call = reply_call(
        client,
        chat_model,
        "actually keep an eye out",
        ToolCall(CONTESTED_GATHERING_TOOL, {"on": True}),
        "Will do.",
    )

    assert "may keep quietly noting" in call.tool_results[0]
    assert me(client, headers)["contested_gathering_enabled"] is True


def test_the_two_sharing_numbers_are_settings_with_hints_and_eval_overrides(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    settings = client.get("/api/admin/settings", headers=admin).json()["settings"]
    choices = client.get("/api/admin/setting-override-choices", headers=admin).json()

    assert {key: settings[key]["value"] for key in SHARING_SETTINGS} == {
        "patterns_shared_per_week": 1,
        "pattern_share_wait_days": 5,
    }
    assert all(settings[key]["hint"] for key in SHARING_SETTINGS)
    assert set(SHARING_SETTINGS) <= {setting["key"] for setting in choices["settings"]}


def test_admins_see_the_kind_that_shares_a_pattern_and_cant_change_what_it_does(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    admin = owner_headers(client, auth_verifier)

    kinds = {kind["name"]: kind for kind in list_kinds(client, admin)}

    assert kinds[NOTICED_KIND]["shares_pattern"] is True
    assert [name for name, kind in kinds.items() if kind["shares_pattern"]] == [
        NOTICED_KIND
    ]


def test_delete_my_data_removes_predictions_and_reactions(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    talk(client, chat_model, clock, "yes, that's me")
    end_with(
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        reactions=[{"pattern": 1, "reaction": "agreed"}],
    )
    assert predictions_of(client.engine, user_id)
    assert reactions_of(client.engine, user_id)

    client.delete("/api/me/data", headers=auth_headers(auth_verifier, "user_maya"))

    assert predictions_of(client.engine, user_id) == []
    assert reactions_of(client.engine, user_id) == []
    assert moves_of(client.engine, user_id) == []


def test_the_migration_keeps_user_data_and_reloads_the_three_prompts(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    database_url: str,
) -> None:
    user_id = ready_to_share(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    share(client, chat_model, clock)
    observations_before = observations_of(client.engine, user_id)
    moves_before = len(moves_of(client.engine, user_id))
    reloaded = (
        "pattern_tagging_prompt",
        "reply_plan_prompt",
        "reply_settings_instructions",
    )
    with client.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE platform_settings SET value = '\"edited\"' "
                "WHERE key = ANY(:keys)"
            ),
            {"keys": list(reloaded)},
        )

    downgrade_to(database_url, "0098")
    try:
        with client.engine.connect() as connection:
            states = connection.execute(text("SELECT state FROM patterns")).scalars()
            assert list(states) == ["suspected"]
            kinds = connection.execute(text("SELECT name FROM check_in_kinds"))
            assert NOTICED_KIND not in set(kinds.scalars())
    finally:
        migrate(database_url)

    assert observations_of(client.engine, user_id) == observations_before
    assert len(moves_of(client.engine, user_id)) == moves_before
    with client.engine.connect() as connection:
        stored = connection.execute(
            text("SELECT count(*) FROM platform_settings WHERE key = ANY(:keys)"),
            {"keys": list(reloaded)},
        ).scalar_one()
        kinds = connection.execute(
            text("SELECT name FROM check_in_kinds WHERE shares_pattern")
        )
        assert list(kinds.scalars()) == [NOTICED_KIND]
        gathering = connection.execute(
            text("SELECT contested_gathering_enabled FROM users")
        )
        assert set(gathering.scalars()) == {True}
    assert stored == 0


def test_users_see_the_kind_that_shares_a_pattern_only_while_sharing_works_for_them(
    client: TestClient, auth_verifier: FakeAuthVerifier, chat_channel: FakeChatChannel
) -> None:
    headers = set_up_user_with_check_ins(client, auth_verifier, chat_channel)

    def kind_names() -> list[str]:
        """The names of the Kinds on Maya's Check-ins page."""
        kinds = client.get("/api/check-ins", headers=headers).json()["kinds"]
        return [kind["name"] for kind in kinds]

    assert NOTICED_KIND not in kind_names()

    turn_sharing_on(client, auth_verifier)

    assert kind_names()[-1] == NOTICED_KIND
