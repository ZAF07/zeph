from datetime import timedelta
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import (
    MIGRATIONS_DIR,
    migrate,
    seed_platform_settings,
)
from companion.core.models import PhotoImage
from tests.conftest import SEED_FILE
from tests.fakes import (
    FakeAuthVerifier,
    FakeChatChannel,
    FakeClock,
    FakePhotoViewer,
    FakeScheduler,
    ScriptedChatModel,
)
from tests.telegram_helpers import (
    auth_headers,
    connect_telegram,
    send_to_webhook,
    telegram_photo_update,
)
from tests.test_message_retention import message_contents, retention
from tests.test_post_conversation import processing_answer, quiet_gap

CAT = "A ginger cat asleep on a sunny windowsill next to a small cactus."
RECEIPT = "A shop receipt for groceries, with a total at the bottom."
CAT_NOTE = "Miso is their cat, who keeps them company when they work from home."
CAT_IMAGE = PhotoImage(content=b"cat-jpeg-bytes", media_type="image/jpeg")


def share_photos_and_end_conversation(
    client: TestClient,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
    answer: str,
) -> None:
    """Send a cat photo and a receipt, let the quiet gap pass and process it."""
    photo_viewer.script(CAT, RECEIPT)
    chat_model.script("what a sleepy cat", "got it")
    send_to_webhook(
        client,
        telegram_photo_update(
            caption="this is Miso", file_unique_id="cat", message_id=10
        ),
    )
    send_to_webhook(
        client, telegram_photo_update(file_unique_id="receipt", message_id=11)
    )
    clock.advance(quiet_gap(seeded_settings) + timedelta(minutes=1))
    chat_model.script_processing(answer)
    scheduler.tick()


def keep_the_cat() -> str:
    """The processing answer that keeps photo 1, the cat, with a note."""
    return processing_answer(photos_to_keep=[{"photo": 1, "note": CAT_NOTE}])


def shared_photos(client: TestClient, headers: dict[str, str]) -> list[dict[str, Any]]:
    """List the User's Shared Photos through the Dashboard API."""
    response = client.get("/api/shared-photos", headers=headers)
    assert response.status_code == 200
    photos: list[dict[str, Any]] = response.json()["photos"]
    return photos


def set_up_user_with_a_shared_cat(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> dict[str, str]:
    """Connect a User and keep their cat photo as a Shared Photo.

    Returns:
        Their Dashboard API headers.
    """
    connect_telegram(client, auth_verifier, chat_channel)
    share_photos_and_end_conversation(
        client,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
        keep_the_cat(),
    )
    return auth_headers(auth_verifier, "user_maya")


def test_picked_photos_become_shared_photos_with_a_note_and_others_are_not_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    sent_at = clock.now()

    share_photos_and_end_conversation(
        client,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
        keep_the_cat(),
    )

    [processing_call] = chat_model.processing_calls
    given = processing_call.history[-1].text
    assert f"[1] {CAT}" in given
    assert f"[2] {RECEIPT}" in given
    [photo] = shared_photos(client, headers)
    assert photo["description"] == CAT
    assert photo["note"] == CAT_NOTE
    assert photo["caption"] == "this is Miso"
    assert photo["sent_at"] == sent_at.isoformat().replace("+00:00", "Z")


def test_photos_the_model_names_wrongly_are_skipped(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")

    share_photos_and_end_conversation(
        client,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
        processing_answer(
            photos_to_keep=[
                {"photo": 7, "note": "no such photo"},
                {"photo": "1", "note": "not a number"},
                {"photo": 2},
                {"photo": 1, "note": CAT_NOTE},
                {"photo": 1, "note": "the same photo again"},
            ]
        ),
    )

    assert [photo["note"] for photo in shared_photos(client, headers)] == [CAT_NOTE]


def test_with_user_memory_off_no_photos_are_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    connect_telegram(client, auth_verifier, chat_channel)
    headers = auth_headers(auth_verifier, "user_maya")
    client.patch("/api/me", json={"user_memory_enabled": False}, headers=headers)

    share_photos_and_end_conversation(
        client,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
        keep_the_cat(),
    )

    assert shared_photos(client, headers) == []


def test_shared_photos_stay_after_message_retention_deletes_their_messages(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_a_shared_cat(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
    )

    clock.advance(retention(seeded_settings) + timedelta(days=1))
    scheduler.tick()

    assert message_contents(engine) == []
    [photo] = shared_photos(client, headers)
    assert photo["description"] == CAT
    assert photo["note"] == CAT_NOTE


def test_a_shared_photo_is_served_through_the_backend(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    chat_channel.photos["file-cat"] = CAT_IMAGE
    headers = set_up_user_with_a_shared_cat(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
    )
    [photo] = shared_photos(client, headers)

    response = client.get(f"/api/shared-photos/{photo['id']}/image", headers=headers)

    assert response.status_code == 200
    assert response.content == CAT_IMAGE.content
    assert response.headers["content-type"] == "image/jpeg"
    assert chat_channel.downloaded_photos[-1] == "file-cat"


def test_a_shared_photo_that_cannot_be_downloaded_has_no_image(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_a_shared_cat(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
    )
    [photo] = shared_photos(client, headers)
    chat_channel.photo_download_failures.append(RuntimeError("file is gone"))

    response = client.get(f"/api/shared-photos/{photo['id']}/image", headers=headers)

    assert response.status_code == 404


def test_a_user_deletes_one_of_their_shared_photos(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_a_shared_cat(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
    )
    [photo] = shared_photos(client, headers)

    response = client.delete(f"/api/shared-photos/{photo['id']}", headers=headers)

    assert response.status_code == 204
    assert shared_photos(client, headers) == []
    again = client.delete(f"/api/shared-photos/{photo['id']}", headers=headers)
    assert again.status_code == 404


def test_a_user_cannot_see_or_delete_another_users_shared_photo(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
    photo_viewer: FakePhotoViewer,
    clock: FakeClock,
    scheduler: FakeScheduler,
    seeded_settings: dict[str, Any],
) -> None:
    headers = set_up_user_with_a_shared_cat(
        client,
        auth_verifier,
        chat_channel,
        chat_model,
        photo_viewer,
        clock,
        scheduler,
        seeded_settings,
    )
    [photo] = shared_photos(client, headers)
    other_headers = auth_headers(auth_verifier, "user_sam")

    assert shared_photos(client, other_headers) == []
    image = client.get(f"/api/shared-photos/{photo['id']}/image", headers=other_headers)
    assert image.status_code == 404
    deleted = client.delete(f"/api/shared-photos/{photo['id']}", headers=other_headers)
    assert deleted.status_code == 404
    assert len(shared_photos(client, headers)) == 1


def test_shared_photos_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/shared-photos").status_code == 401


def stored_memory_processing_prompt(engine: Engine) -> str:
    """Read the stored memory processing prompt."""
    with engine.connect() as connection:
        prompt: str = connection.execute(
            text(
                "SELECT value FROM platform_settings "
                "WHERE key = 'memory_processing_prompt'"
            )
        ).scalar_one()
    return prompt


def test_an_existing_install_loads_the_new_memory_processing_prompt(
    engine: Engine, database_url: str, seeded_settings: dict[str, Any]
) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.downgrade(config, "0017")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO platform_settings (key, value, updated_at) "
                    "VALUES ('memory_processing_prompt', '\"The old prompt.\"', now())"
                )
            )
        assert stored_memory_processing_prompt(engine) == "The old prompt."
    finally:
        migrate(database_url)

    seed_platform_settings(engine, SEED_FILE)

    prompt = stored_memory_processing_prompt(engine)
    assert prompt == seeded_settings["memory_processing_prompt"]
    assert "photos_to_keep" in prompt
