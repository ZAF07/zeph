from companion.core.models import MoodIntensity, UnderstandingForm
from companion.core.understanding import may_send_photo


def form(struggling: bool, asked_for_photo: bool) -> UnderstandingForm:
    """An Understanding form that differs only in the two photo fields."""
    return UnderstandingForm(
        need="Be heard",
        nuance="",
        mood="scared",
        intensity=MoodIntensity.HIGH,
        cause_known=True,
        struggling=struggling,
        asked_for_photo=asked_for_photo,
    )


def test_a_photo_may_be_sent_unless_the_user_is_struggling_and_did_not_ask() -> None:
    assert may_send_photo(form(struggling=False, asked_for_photo=False))
    assert may_send_photo(form(struggling=False, asked_for_photo=True))
    assert may_send_photo(form(struggling=True, asked_for_photo=True))
    assert not may_send_photo(form(struggling=True, asked_for_photo=False))
