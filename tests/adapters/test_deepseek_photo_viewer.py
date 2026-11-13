import base64

from langchain_core.messages import HumanMessage, SystemMessage

from companion.adapters.deepseek.photo_viewer import to_photo_messages
from companion.core.models import PhotoImage


def test_the_photo_goes_in_a_user_message_after_the_instructions() -> None:
    photo = PhotoImage(content=b"png-bytes", media_type="image/png")

    messages = to_photo_messages("Describe the photo.", photo)

    data_url = "data:image/png;base64," + base64.b64encode(b"png-bytes").decode()
    assert messages == [
        SystemMessage("Describe the photo."),
        HumanMessage(content=[{"type": "image_url", "image_url": {"url": data_url}}]),
    ]
