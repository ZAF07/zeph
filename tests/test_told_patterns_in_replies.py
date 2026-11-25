from dataclasses import replace
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from companion.core.models import (
    CatalogPattern,
    NarrowingTag,
    ObservationDirection,
    PatternNarrowing,
    PatternState,
)
from companion.core.pattern_sharing import (
    Showing,
    describe_told,
    format_asked_for_patterns_for_reply,
    told_patterns_in_mind,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import connect_telegram, owner_headers
from tests.test_explorations import talk
from tests.test_features import switch_for_user
from tests.test_pattern_sharing import (
    APPROVED_WORDING,
    CONTESTED_HEADER,
    OFFER_HEADER,
    end_with,
    predictions_of,
    ready_to_share,
    share,
    turn_sharing_on,
)
from tests.test_patterns_dashboard import set_state, told_belonging
from tests.test_ready_gate import belonging
from tests.test_ready_gate_rules import BELONG, NOW, PATTERN_TYPES, TODAY, WORTH, story

TOLD_HEADER = "Patterns you have told them"
STILL_GETTING_TO_KNOW = "you are still getting to know them"
NONE_TO_TELL = "You have no pattern you may tell them now"
ASKED = "what patterns do you see in me?"


def told(state: PatternState, pattern_type_id: str = BELONG) -> CatalogPattern:
    """A User's Pattern in the given state, told to them 30 days ago."""
    shared_at = NOW - timedelta(days=30)
    return CatalogPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_type_id=pattern_type_id,
        state=state,
        started_at=shared_at,
        updated_at=shared_at,
        shared_at=shared_at,
        shared_wording="The words Zeph told it in.",
    )


def test_only_patterns_being_tested_or_confirmed_come_to_mind_oldest_told_first() -> (
    None
):
    tested = replace(told(PatternState.SHARED), shared_at=NOW - timedelta(days=5))
    confirmed = told(PatternState.CONFIRMED, WORTH)
    others = [
        told(state, f"ACH.GOAL.{state.name}")
        for state in PatternState
        if state not in {PatternState.SHARED, PatternState.CONFIRMED}
    ]

    in_mind = told_patterns_in_mind([tested, *others, confirmed], PATTERN_TYPES, [], {})

    assert [(item.number, item.pattern.id) for item in in_mind] == [
        (1, confirmed.id),
        (2, tested.id),
    ]
    assert {item.wording for item in in_mind} == {"The words Zeph told it in."}


def test_a_told_pattern_says_where_it_last_showed_up_and_was_acted_against() -> None:
    pattern = told(PatternState.SHARED)
    mei_thread = uuid4()
    earlier = replace(story(about="Jun, a friend"), day=TODAY - timedelta(days=9))
    newest = story(about="Mei, their sister", thread=mei_thread)
    unclear = replace(story(about="Priya", second=WORTH), day=TODAY)
    against = replace(
        story(about="Dana", direction=ObservationDirection.AGAINST),
        day=TODAY - timedelta(days=2),
    )

    [in_mind] = told_patterns_in_mind(
        [pattern],
        PATTERN_TYPES,
        [earlier, against, newest, unclear],
        {mei_thread: "Falling-out with Mei"},
    )

    assert in_mind.last_showed == Showing(
        TODAY, "Mei, their sister", "Falling-out with Mei"
    )
    assert in_mind.last_acted_against == Showing(
        TODAY - timedelta(days=2), "Dana", None
    )


def test_the_reply_plan_reads_each_told_pattern_with_how_it_stands() -> None:
    narrowed = replace(
        told(PatternState.CONFIRMED),
        narrowings=(
            PatternNarrowing(
                tag=NarrowingTag.RELATIONSHIP,
                holds_with=("family",),
                not_with=("partner",),
            ),
        ),
    )
    [in_mind] = told_patterns_in_mind(
        [narrowed], PATTERN_TYPES, [story(about="Mei")], {}
    )

    described = describe_told([in_mind])

    assert TOLD_HEADER in described
    assert (
        "[1] (confirmed) The words Zeph told it in. It shows with family; "
        "not with partner. Last showed up: 25 Nov 2026, about Mei."
    ) in described
    assert "acted against" not in described.split("[1]")[1]
    assert describe_told([]) == ""


def test_asked_for_patterns_the_reply_may_recall_only_what_it_told_them() -> None:
    in_mind = told_patterns_in_mind([told(PatternState.SHARED)], PATTERN_TYPES, [], {})

    with_one = format_asked_for_patterns_for_reply(in_mind)
    with_none = format_asked_for_patterns_for_reply([])

    assert "(being tested) The words Zeph told it in." in with_one
    assert "Tell them no other pattern" in with_one
    assert STILL_GETTING_TO_KNOW in with_none
    assert "don't call anything a pattern" in with_none


def test_the_reply_plan_is_shown_the_pattern_zeph_told_them_and_may_name_it(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    end_with(chat_model, clock, scheduler, seeded_settings)

    saw = talk(
        client, chat_model, clock, "Mei asked again and I said yes", named_pattern=1
    )
    while_tested = chat_model.calls[-1].instructions
    set_state(
        client.engine, belonging(client.engine, user_id).id, PatternState.CONFIRMED
    )
    talk(client, chat_model, clock, "and Jun too", named_pattern=1)
    once_confirmed = chat_model.calls[-1].instructions
    talk(client, chat_model, clock, "anyway", named_pattern=7)

    told_part = saw[saw.index(TOLD_HEADER) :].split("\n\n")[0]
    assert f"[1] (being tested) {APPROVED_WORDING}" in told_part
    assert "Last showed up: " in told_part
    assert "links to something you told them before" in while_tested
    assert APPROVED_WORDING in while_tested
    assert "the thing we're testing" in while_tested
    assert "you may say it plainly" in once_confirmed
    assert "links to something you told them" not in chat_model.calls[-1].instructions


def test_a_pattern_they_disagreed_with_is_never_among_those_a_reply_may_name(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    set_state(
        client.engine, belonging(client.engine, user_id).id, PatternState.CONTESTED
    )

    saw = talk(client, chat_model, clock, "hello again", named_pattern=1)

    assert TOLD_HEADER not in saw
    assert CONTESTED_HEADER in saw
    assert "links to something you told them" not in chat_model.calls[-1].instructions


@pytest.mark.parametrize("why", ["struggling", "sharing_off"])
def test_no_told_pattern_is_shown_while_struggling_or_with_pattern_sharing_off(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    why: str,
) -> None:
    user_id = told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )
    if why == "struggling":
        chat_model.script_understanding(understanding_answer(struggling=True))
    else:
        admin = owner_headers(client, auth_verifier)
        switch_for_user(client, admin, user_id, "pattern_sharing", "off")

    saw = talk(
        client,
        chat_model,
        clock,
        "I can't cope. what patterns do you see in me?",
        named_pattern=1,
        asked_for_patterns=True,
    )

    told_reply = chat_model.calls[-1].instructions
    assert TOLD_HEADER not in saw
    assert APPROVED_WORDING not in told_reply
    assert NONE_TO_TELL in told_reply
    assert "passed your tests" not in told_reply


def test_asked_for_patterns_with_nothing_ready_zeph_says_it_is_still_getting_to_know(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    turn_sharing_on(client, auth_verifier)

    talk(client, chat_model, clock, "hi")
    not_asked = chat_model.calls[-1].instructions
    talk(client, chat_model, clock, ASKED, asked_for_patterns=True)
    asked = chat_model.calls[-1].instructions

    assert STILL_GETTING_TO_KNOW not in not_asked
    assert STILL_GETTING_TO_KNOW in asked
    assert "don't call anything a pattern" in asked


def test_asked_for_patterns_with_one_ready_it_is_shared_properly(
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

    told_reply = share(client, chat_model, clock, message=ASKED)
    saw = chat_model.reply_plan_calls[-1].history[0].text

    assert OFFER_HEADER in saw
    assert "Tell them this Pattern in this reply" in told_reply
    assert STILL_GETTING_TO_KNOW not in told_reply
    assert belonging(client.engine, user_id).state == PatternState.SHARED
    assert len(predictions_of(client.engine, user_id)) == 1


def test_asked_for_patterns_a_ready_one_is_shared_even_if_the_plan_did_not_say_so(
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

    talk(client, chat_model, clock, ASKED, asked_for_patterns=True, share_pattern=False)

    assert "Tell them this Pattern in this reply" in chat_model.calls[-1].instructions
    assert len(chat_model.shared_check_calls) == 1


def test_asked_for_patterns_after_one_was_told_the_reply_recalls_it_and_no_other(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    told_belonging(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
    )

    talk(client, chat_model, clock, ASKED, asked_for_patterns=True)

    asked = chat_model.calls[-1].instructions
    assert f"- (being tested) {APPROVED_WORDING}" in asked
    assert "Tell them no other pattern" in asked
    assert STILL_GETTING_TO_KNOW not in asked
