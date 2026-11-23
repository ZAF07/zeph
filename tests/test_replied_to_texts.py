from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakeEmbedder,
    FakeScheduler,
    ScriptedChatModel,
    understanding_answer,
)
from tests.telegram_helpers import (
    OWNER_TELEGRAM_USER_ID,
    TELEGRAM_CHAT_ID,
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    post_to_webhook,
    send_to_webhook,
    telegram_reply_update,
    telegram_text_update,
)
from tests.test_life_threads import end_conversation, new_thread, reply_plan_sees
from tests.test_model_call_log import newest_call
from tests.test_post_conversation import processing_answer, quiet_gap
from tests.test_recent_messages import given_text, newest_reply_steps
from tests.test_safeguard import use_simple_crisis_reply

QUESTION = "have you told your mum about the job yet?"
ANSWER = "not yet, scared tbh"
SEEN_AS_REPLY = f'(replying to the Companion\'s text from 3 Nov 2025, "{QUESTION}")'
REPLY_SEES = f'(replying to your text from 3 Nov 2025, "{QUESTION}") {ANSWER}'


def replied_to_texts_kept(engine: Engine) -> int:
    """Count the saved messages that keep a Replied-to Text."""
    with engine.connect() as connection:
        count: int = connection.execute(
            text(
                "SELECT count(*) FROM conversation_messages "
                "WHERE replied_to IS NOT NULL"
            )
        ).scalar_one()
    return count


def test_a_reply_to_zephs_text_reaches_the_understanding_reply_plan_and_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")

    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert f"Person: {SEEN_AS_REPLY} {ANSWER}" in given_text(call)
    assert reply.history[-1].text == REPLY_SEES


def test_a_reply_to_the_users_own_text_reads_as_their_own_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("ugh, still?")

    send_to_webhook(
        client,
        telegram_reply_update(
            "like I said", {"text": "I hate my commute"}, from_companion=False
        ),
    )

    for call in newest_reply_steps(chat_model):
        assert (
            '(replying to their own text from 3 Nov 2025, "I hate my commute") '
            "like I said"
        ) in given_text(call)


def test_a_highlighted_part_is_shown_instead_of_the_whole_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("what did she say?")

    send_to_webhook(
        client,
        telegram_reply_update(
            "this",
            {"text": "work was rough. also mum called"},
            from_companion=False,
            quote="also mum called",
        ),
    )

    for call in newest_reply_steps(chat_model):
        assert '"also mum called") this' in given_text(call)
        assert "work was rough" not in given_text(call)


def test_a_reply_to_a_photo_or_sticker_says_so_with_any_caption(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    photo = [{"file_id": "file-cat", "file_unique_id": "cat", "width": 9}]
    sticker = {"file_id": "file-hug", "file_unique_id": "hug", "emoji": "🤗"}
    chat_model.script("aw")

    post_to_webhook(
        client,
        telegram_reply_update(
            "so cute", {"photo": photo, "caption": "my cat"}, from_companion=False
        ),
    )
    post_to_webhook(client, telegram_reply_update("thanks", {"sticker": sticker}))
    send_to_webhook(
        client, telegram_reply_update("and this", {"photo": photo}, message_id=12)
    )

    understanding = newest_reply_steps(chat_model)[0]
    assert (
        '(replying to their own photo from 3 Nov 2025, "my cat") so cute'
        in given_text(understanding)
    )
    assert (
        '(replying to the Companion\'s sticker from 3 Nov 2025, "🤗") thanks'
        in given_text(understanding)
    )
    assert "(replying to the Companion's photo from 3 Nov 2025) and this" in given_text(
        understanding
    )


def test_each_text_of_a_message_shows_the_text_it_replies_to(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("lots going on")

    post_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))
    post_to_webhook(client, telegram_text_update("anyway"))
    send_to_webhook(
        client,
        telegram_reply_update("better now", {"text": "how's the cold?"}, message_id=12),
    )

    reply = newest_reply_steps(chat_model)[-1]
    assert reply.history[-1].text == "\n".join(
        [
            REPLY_SEES,
            "anyway",
            '(replying to your text from 3 Nov 2025, "how\'s the cold?") better now',
        ]
    )


def test_later_replies_in_the_conversation_still_see_the_link(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")
    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))
    chat_model.script("you'll find the moment")

    send_to_webhook(client, telegram_text_update("maybe this weekend"))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert f"Person: {SEEN_AS_REPLY} {ANSWER}" in given_text(call)
    assert reply.history[0].text == REPLY_SEES


def test_a_new_conversation_still_sees_the_link_in_the_recent_messages(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")
    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    chat_model.script("hey you")

    send_to_webhook(client, telegram_text_update("morning"))

    understanding, reply_plan, reply = newest_reply_steps(chat_model)
    for call in (understanding, reply_plan):
        assert "New Conversation" in given_text(call)
        assert f"Person: {SEEN_AS_REPLY} {ANSWER}" in given_text(call)
    assert reply.history[0].text == REPLY_SEES


def test_the_model_call_log_shows_the_replied_to_text_in_an_admins_own_chat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    admin = connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")

    send_to_webhook(
        client,
        telegram_reply_update(
            ANSWER, {"text": QUESTION}, telegram_user_id=OWNER_TELEGRAM_USER_ID
        ),
    )

    understanding = newest_call(client, admin, "understanding")
    reply = newest_call(client, admin, "reply")
    assert SEEN_AS_REPLY in understanding["content"]["history"][0]["text"]
    assert reply["content"]["history"][-1]["text"] == REPLY_SEES


def test_delete_my_data_removes_the_replied_to_text_with_the_text(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")
    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))
    assert replied_to_texts_kept(engine) == 1

    response = client.delete(
        "/api/me/data", headers=auth_headers(auth_verifier, "user_maya")
    )

    assert response.status_code == 204
    assert replied_to_texts_kept(engine) == 0


def test_the_safeguard_reads_a_text_with_its_replied_to_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")

    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))

    assert chat_model.safeguard_calls[-1].history[0].text == (
        f"Latest message to classify:\nPerson: {SEEN_AS_REPLY} {ANSWER}"
    )


def test_yes_as_a_reply_to_zephs_self_harm_question_gets_the_crisis_reply(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    use_simple_crisis_reply(client, owner_headers(client, auth_verifier))
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script_safeguard("suicide_or_self_harm")
    question = "are you thinking about hurting yourself?"

    send_to_webhook(client, telegram_reply_update("yes", {"text": question}))

    assert f'"{question}") yes' in chat_model.safeguard_calls[-1].history[0].text
    assert chat_channel.texts_sent_to(TELEGRAM_CHAT_ID)[-1].startswith(
        "I'm an AI. Please reach out:"
    )
    assert chat_model.calls == []


def test_recall_searches_with_the_replied_to_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("oh, that's a lot to carry")

    send_to_webhook(client, telegram_reply_update(ANSWER, {"text": QUESTION}))

    searches = [query for query in embedder.queries if ANSWER in query]
    assert searches
    assert all(f"{QUESTION}\n{ANSWER}" in query for query in searches)


def test_a_thread_close_only_to_the_replied_to_text_comes_to_mind(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "training is going badly",
        [
            new_thread(
                title="Marathon training",
                story="Knee pain during long runs.",
                people=("Berlin",),
            )
        ],
    )
    clock.advance(timedelta(days=30))
    hurts = understanding_answer(means="It hurts.")
    chat_model.script_understanding(hurts, hurts)

    plain = reply_plan_sees(client, chat_model, "ugh")
    chat_model.script("oh no")
    send_to_webhook(
        client,
        telegram_reply_update(
            "ugh", {"text": "how's the knee pain during long runs?"}, message_id=12
        ),
    )
    replied = chat_model.reply_plan_calls[-1].history[0].text

    assert "Marathon training" not in plain
    assert "Marathon training" in replied
