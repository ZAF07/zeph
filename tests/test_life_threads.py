import json
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

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
    auth_headers,
    connect_owner_telegram,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)
from tests.test_older_summaries import set_settings
from tests.test_post_conversation import (
    have_conversation,
    processing_answer,
    quiet_gap,
)

MEI_STORY = (
    "Fell out with their sister Mei in February over money for their mum's care."
)


def thread_keeping_answer(threads: list[dict[str, Any]]) -> str:
    """Build the JSON the Life Thread keeping model answers with."""
    return json.dumps({"threads": threads})


def new_thread(
    title: str = "Falling-out with Mei",
    story: str = MEI_STORY,
    people: tuple[str, ...] = ("Mei", "sister"),
    is_open: bool = True,
) -> dict[str, Any]:
    """Build a new Thread as the keeping model writes it."""
    return {"title": title, "story": story, "people": list(people), "open": is_open}


def end_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    text: str,
    threads: list[dict[str, Any]],
) -> None:
    """Have a one-message Conversation whose end keeps the given Threads."""
    chat_model.script_thread_keeping(thread_keeping_answer(threads))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        text,
        processing_answer(summary="Talked about family.", mood="sad"),
    )


def understanding_sees(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a message and return what its Understanding was given."""
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(text))
    return chat_model.understanding_calls[-1].history[0].text


def test_a_conversation_end_starts_a_thread_and_naming_someone_in_it_brings_it_back(
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
        "Mei and I had a huge fight about mum's care",
        [new_thread()],
    )
    clock.advance(timedelta(days=270))

    seen = understanding_sees(client, chat_model, "Mei's wedding is next week!")

    assert "[1] Falling-out with Mei (open" in seen
    assert MEI_STORY in seen


def bring_up_thread_one(chat_model: ScriptedChatModel, how: str = "lead") -> None:
    """Script the next Understanding to bring up the first reminded Thread."""
    chat_model.script_understanding(
        understanding_answer(bring_up=[{"thread": 1, "how": how}], threads_touched=[1])
    )


def reply_instructions(
    client: TestClient, chat_model: ScriptedChatModel, text: str
) -> str:
    """Send a message and return what its reply call was told."""
    chat_model.script("mm, tell me more")
    send_to_webhook(client, telegram_text_update(text))
    return chat_model.calls[-1].instructions


def start_mei_thread(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    """Have a Conversation whose end starts the falling-out with Mei Thread."""
    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Mei and I had a huge fight about mum's care",
        [new_thread()],
    )


def test_a_message_close_in_meaning_to_a_story_brings_it_and_a_weak_match_does_not(
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

    close = understanding_sees(client, chat_model, "knee pain on long runs")
    clock.advance(timedelta(days=2))
    weak = understanding_sees(client, chat_model, "the knee is fine")

    assert "Marathon training" in close
    assert "Marathon training" not in weak


def test_open_threads_come_before_settled_ones_up_to_the_admin_set_number(
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
        "Mei helped me move flat, all sorted now",
        [new_thread(title="Moving flat with Mei", story="Moved.", is_open=False)],
    )
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)

    both = understanding_sees(client, chat_model, "I saw Mei today")
    set_settings(client, auth_verifier, {"life_threads_per_reply": 1})
    one = understanding_sees(client, chat_model, "Mei called again")

    assert "[1] Falling-out with Mei (open" in both
    assert "[2] Moving flat with Mei (settled" in both
    assert "Falling-out with Mei" in one
    assert "Moving flat with Mei" not in one


def test_the_admin_sets_how_close_a_story_must_be(
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
        [new_thread(title="Marathon training", story="Knee pain.", people=())],
    )

    set_settings(client, auth_verifier, {"life_threads_closeness_percent": 20})
    loose = understanding_sees(client, chat_model, "the knee is fine")
    set_settings(client, auth_verifier, {"life_threads_closeness_percent": 100})
    strict = understanding_sees(client, chat_model, "knee pain again")

    assert "Marathon training" in loose
    assert "Marathon training" not in strict


def test_a_thread_brought_up_reaches_the_reply_with_how_and_its_story(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=270))

    bring_up_thread_one(chat_model)
    instructions = reply_instructions(
        client, chat_model, "my sister's wedding is next week"
    )

    assert MEI_STORY in instructions
    assert "Bring up, the way a friend who remembers would:" in instructions
    assert "- Falling-out with Mei: lead with it." in instructions


def test_a_thread_left_alone_reaches_the_reply_without_its_story(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)

    chat_model.script_understanding(
        understanding_answer(
            left_alone=[{"thread": 1, "reason": "they're grieving their dog"}],
            threads_touched=[1],
        )
    )
    instructions = reply_instructions(client, chat_model, "Mei sent flowers")

    assert "- Falling-out with Mei: they're grieving their dog" in instructions
    assert MEI_STORY not in instructions
    assert "Bring up" not in instructions


def test_a_thread_raised_earlier_in_the_conversation_is_not_raised_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    bring_up_thread_one(chat_model)
    reply_instructions(client, chat_model, "my sister's wedding is next week")

    bring_up_thread_one(chat_model)
    seen_again = understanding_sees(client, chat_model, "Mei wants me there")
    second_reply = chat_model.calls[-1].instructions

    assert (
        "Don't bring it up: you already brought it up in this Conversation."
        in seen_again
    )
    assert "Bring up" not in second_reply
    assert (
        "- Falling-out with Mei: you already brought it up in this Conversation"
        in second_reply
    )


def raise_and_react(
    client: TestClient,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    reaction: str,
) -> None:
    """Bring up the Mei Thread in a Conversation that ends with a reaction."""
    bring_up_thread_one(chat_model)
    chat_model.script_thread_keeping(
        thread_keeping_answer([{"thread": 1, "reaction": reaction}])
    )
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Mei is getting married",
        processing_answer(summary="Mentioned Mei's wedding.", mood="flat"),
    )


def test_a_brushed_off_thread_waits_the_admin_set_time_before_it_can_come_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    raise_and_react(
        client, chat_model, clock, scheduler, seeded_settings, "brushed_off"
    )

    clock.advance(timedelta(days=3))
    too_soon = understanding_sees(client, chat_model, "Mei texted me")
    clock.advance(timedelta(days=12))
    after_the_wait = understanding_sees(client, chat_model, "Mei texted me again")
    set_settings(client, auth_verifier, {"life_thread_brushed_off_wait_days": 30})
    longer_wait = understanding_sees(client, chat_model, "Mei called")

    assert "they brushed it off. Don't bring it up: they brushed it off" in too_soon
    assert "Don't bring it up" not in after_the_wait
    assert "Last brought up" in after_the_wait
    assert "Don't bring it up: they brushed it off" in longer_wait


def test_a_thread_they_asked_to_drop_is_never_offered_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    raise_and_react(
        client, chat_model, clock, scheduler, seeded_settings, "asked_to_drop"
    )
    clock.advance(timedelta(days=400))

    bring_up_thread_one(chat_model)
    seen = understanding_sees(client, chat_model, "Mei had a baby")
    instructions = chat_model.calls[-1].instructions

    assert "Don't bring it up: they asked you to drop it" in seen
    assert "Bring up" not in instructions


def test_conversation_end_updates_a_thread_and_shows_the_keeper_what_was_raised(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    bring_up_thread_one(chat_model)
    settled_story = "Fell out with Mei in February; made up at her wedding in November."
    chat_model.script_thread_keeping(
        thread_keeping_answer(
            [
                {
                    "thread": 1,
                    "story": settled_story,
                    "people": ["Mei", "sister", "wedding"],
                    "open": False,
                    "reaction": "engaged",
                }
            ]
        )
    )
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Mei and I hugged it out at the wedding",
        processing_answer(summary="Made up with Mei.", mood="relieved"),
    )
    keeper_saw = chat_model.thread_keeping_calls[-1].history[0].text

    seen = understanding_sees(client, chat_model, "the wedding photos came")

    assert "[1] Falling-out with Mei (open" in keeper_saw
    assert "Brought up in this Conversation." in keeper_saw
    assert "Mei and I hugged it out at the wedding" in keeper_saw
    assert "[1] Falling-out with Mei (settled" in seen
    assert settled_story in seen
    assert "they engaged." in seen


def test_with_user_memory_off_no_thread_is_kept_but_saved_ones_are_still_used(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    end_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Starting a new job at Acme",
        [new_thread(title="New job at Acme", story="Starts Monday.", people=("Acme",))],
    )
    seen = understanding_sees(client, chat_model, "Mei and Acme both called")

    assert len(chat_model.thread_keeping_calls) == 1
    assert "Falling-out with Mei" in seen
    assert "New job at Acme" not in seen


def test_admins_see_how_many_life_threads_each_user_has(
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
        "Mei and I fell out, and I'm job hunting",
        [new_thread(), new_thread(title="Job hunt", story="Applying.", people=())],
    )

    users = client.get(
        "/api/admin/users", headers=owner_headers(client, auth_verifier)
    ).json()["users"]

    counts = {user["email"]: user["life_thread_count"] for user in users}
    assert counts["user_maya@example.com"] == 2
    assert MEI_STORY not in json.dumps(users)


def test_only_the_users_own_threads_are_found(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_owner_telegram(client, auth_verifier, chat_channel)
    chat_model.script_thread_keeping(thread_keeping_answer([new_thread()]))
    chat_model.script("mm, I hear you")
    send_to_webhook(
        client,
        telegram_text_update(
            "Mei and I fell out", OWNER_TELEGRAM_USER_ID, username="owner_tg"
        ),
    )
    clock.advance(quiet_gap(seeded_settings) * 2)
    chat_model.script_processing(processing_answer())
    scheduler.tick()
    connect_telegram(client, auth_verifier, chat_channel)

    seen = understanding_sees(client, chat_model, "Mei's wedding is next week")

    assert "Falling-out with Mei" not in seen


def test_a_failed_understanding_still_gives_the_reply_the_threads_not_held_back(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    clock.advance(timedelta(days=30))

    chat_model.script_understanding(RuntimeError("model is down"))
    instructions = reply_instructions(client, chat_model, "Mei's wedding is soon")

    assert MEI_STORY in instructions
    assert "Bring up" not in instructions
    assert chat_channel.texts_sent_to(5551001)[-1] == "mm, tell me more"


def test_threads_are_still_found_by_name_when_embedding_fails(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    embedder: FakeEmbedder,
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    embedder.failure = RuntimeError("embedding model is down")

    seen = understanding_sees(client, chat_model, "my sister's wedding is soon")

    assert "Falling-out with Mei" in seen


def test_a_failing_thread_keeper_still_saves_the_summary_and_is_not_retried(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    chat_model.script_thread_keeping(RuntimeError("model is down"))
    have_conversation(
        client,
        chat_model,
        clock,
        scheduler,
        seeded_settings,
        "Mei and I fell out",
        processing_answer(summary="Fell out with Mei."),
    )
    scheduler.tick()

    summaries = client.get("/api/conversation-summaries", headers=headers).json()
    assert [item["summary"] for item in summaries["summaries"]] == [
        "Fell out with Mei."
    ]
    assert len(chat_model.thread_keeping_calls) == 1


def test_a_person_written_with_a_note_in_brackets_is_found_by_either_word(
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
        "Mei and I had a huge fight about mum's care",
        [new_thread(people=("Mei (sister)", "Aunt Rosa"))],
    )

    by_relation = understanding_sees(client, chat_model, "my sister's wedding")
    clock.advance(quiet_gap(seeded_settings) * 2)
    by_full_name = understanding_sees(client, chat_model, "aunt rosa is coming")
    clock.advance(quiet_gap(seeded_settings) * 2)
    by_part_of_a_name = understanding_sees(client, chat_model, "Rosa is coming")

    assert "Falling-out with Mei" in by_relation
    assert "Falling-out with Mei" in by_full_name
    assert "Falling-out with Mei" not in by_part_of_a_name


def test_raising_a_brushed_off_thread_again_with_user_memory_off_keeps_the_wait(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    start_mei_thread(client, chat_model, clock, scheduler, seeded_settings)
    raise_and_react(
        client, chat_model, clock, scheduler, seeded_settings, "brushed_off"
    )
    clock.advance(timedelta(days=15))
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)
    raise_and_react(client, chat_model, clock, scheduler, seeded_settings, "engaged")

    clock.advance(timedelta(days=3))
    seen = understanding_sees(client, chat_model, "Mei texted me")

    assert "Don't bring it up: they brushed it off" in seen
