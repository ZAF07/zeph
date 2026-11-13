from fastapi.testclient import TestClient

from companion.core.models import PhotoImage
from evals.cases import IMAGES_DIR
from tests.fakes import FakeChatChannel
from tests.telegram_helpers import send_to_webhook, telegram_photo_update

MEDIA_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def send_test_photo(
    client: TestClient, chat_channel: FakeChatChannel, file_name: str, caption: str
) -> None:
    """Send a test image through the webhook as a photo.

    The fake chat channel serves the image when the photo service downloads
    it, so the real photo viewer looks at the real image.

    Args:
        client: The backend's test client.
        chat_channel: The fake chat channel, which serves the image.
        file_name: The image's file name in `evals/images/`.
        caption: The photo's caption; "" for none.
    """
    image_file = IMAGES_DIR / file_name
    update = telegram_photo_update(caption or None, file_unique_id=image_file.stem)
    largest_file_id = update["message"]["photo"][-1]["file_id"]
    chat_channel.photos[largest_file_id] = PhotoImage(
        content=image_file.read_bytes(), media_type=MEDIA_TYPES[image_file.suffix]
    )
    assert send_to_webhook(client, update) == 200
