from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.recent_messages import RecentMessages
from companion.core.reply_tools import ReplyGuidance, ReplyOffer
from companion.core.response_composition import (
    ANSWER_THE_QUESTION,
    ASKED_NOW_HEADING,
    BOUNDARIES_HEADING,
    GUIDANCE_HEADING,
    MEMORY_HEADING,
    OPTIONAL_EXTRAS_HEADING,
    PRIORITY_ORDER,
    write_instructions,
)
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    ScriptedChatModel,
)
from tests.telegram_helpers import send_to_webhook, telegram_text_update
from tests.test_check_in_sending import ONE_DAY, set_up_user_with_check_ins
from tests.test_reply_tools import (
    FakeProvider,
    add_user,
    build_composer,
    snapshot_for,
)
from tests.test_woven_in_check_ins import NOTE, weave_plan

QUESTION = "honestly what do you think I should do about the job?"


def positions(instructions: str, *pieces: str) -> list[int]:
    """Find where each piece starts in the instructions, failing if one is missing."""
    found = [instructions.find(piece) for piece in pieces]
    assert -1 not in found, dict(zip(pieces, found, strict=True))
    return found


def test_the_sections_come_in_priority_order_with_the_clash_rule_once() -> None:
    instructions = write_instructions(
        voice="You are Zeph.",
        response_prompt="Reply in short texts.",
        boundaries=["Leave alone: their dog."],
        asked_now=["You can search the web."],
        guidance="Lead with a real read.",
        memory="They work at a bank.",
        optional_extras=["A Check-in is due."],
    )

    order = positions(
        instructions,
        "You are Zeph.",
        "Reply in short texts.",
        PRIORITY_ORDER,
        BOUNDARIES_HEADING,
        "Leave alone: their dog.",
        ASKED_NOW_HEADING,
        ANSWER_THE_QUESTION,
        "You can search the web.",
        GUIDANCE_HEADING,
        "Lead with a real read.",
        MEMORY_HEADING,
        "They work at a bank.",
        OPTIONAL_EXTRAS_HEADING,
        "A Check-in is due.",
    )
    assert order == sorted(order)
    assert instructions.count("the higher one wins") == 1


def test_a_level_with_nothing_in_it_is_left_out_but_the_question_rule_stays() -> None:
    instructions = write_instructions(
        voice="You are Zeph.",
        response_prompt="Reply in short texts.",
        boundaries=[""],
        asked_now=[],
        guidance="",
        memory="",
        optional_extras=["", ""],
    )

    assert BOUNDARIES_HEADING not in instructions
    assert GUIDANCE_HEADING not in instructions
    assert MEMORY_HEADING not in instructions
    assert OPTIONAL_EXTRAS_HEADING not in instructions
    assert f"{ASKED_NOW_HEADING}\n\n{ANSWER_THE_QUESTION}" in instructions


def test_the_composer_puts_each_input_at_its_level(engine: Engine) -> None:
    repositories = build_postgres_repositories(engine)
    user = add_user(repositories)
    chat_model = ScriptedChatModel()
    chat_model.script("hey")
    composer = build_composer(
        repositories,
        chat_model,
        [FakeProvider(ReplyOffer(instructions="You can change their settings."))],
    )

    composer.compose(
        RecentMessages(user.id, []),
        snapshot_for(user),
        memory="They work at a bank.",
        knowledge="Breathing helps.",
        data_deletion_note="They cancelled deleting their data.",
        guidance=ReplyGuidance(
            boundaries="Leave alone: their dog.",
            plan="Lead with a real read.",
            curiosities="Ask about the trip.",
        ),
        optional_offers=[ReplyOffer(instructions="A Check-in is due.")],
    )

    [call] = chat_model.calls
    order = positions(
        call.instructions,
        "They cancelled deleting their data.",
        "Leave alone: their dog.",
        ANSWER_THE_QUESTION,
        "You can change their settings.",
        "Lead with a real read.",
        "They work at a bank.",
        OPTIONAL_EXTRAS_HEADING,
        "A Check-in is due.",
        "Ask about the trip.",
        "Breathing helps.",
    )
    assert order == sorted(order)


def test_a_direct_question_is_answered_before_any_optional_extra(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
) -> None:
    set_up_user_with_check_ins(client, auth_verifier, chat_channel)
    clock.advance(ONE_DAY - timedelta(minutes=5))
    chat_model.script("oh no, what happened?")
    send_to_webhook(client, telegram_text_update("work was a lot today"))
    clock.advance(timedelta(minutes=5))
    chat_model.script_reply_plan(weave_plan())
    chat_model.script("here's my honest read")

    send_to_webhook(client, telegram_text_update(QUESTION))

    reply_call = chat_model.calls[-1]
    assert QUESTION in reply_call.history[-1].text
    question_at, extras_at, check_in_at = positions(
        reply_call.instructions,
        ANSWER_THE_QUESTION,
        OPTIONAL_EXTRAS_HEADING,
        NOTE,
    )
    assert question_at < extras_at < check_in_at
