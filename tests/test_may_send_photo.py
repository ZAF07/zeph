from companion.core.models import MoodIntensity, ReplyPlanForm, UnderstandingForm
from companion.core.reply_plan import may_send_photo


def understanding(struggling: bool, asked_for_photo: bool) -> UnderstandingForm:
    """An Understanding form that differs only in the two photo fields."""
    return UnderstandingForm(
        mood="scared",
        intensity=MoodIntensity.HIGH,
        cause_known=True,
        struggling=struggling,
        asked_for_photo=asked_for_photo,
    )


def plan(photo_fits: bool) -> ReplyPlanForm:
    """A Reply Plan form that differs only in whether a photo fits."""
    return ReplyPlanForm(need="Be heard", photo_fits=photo_fits)


def test_a_photo_may_be_sent_unless_the_user_is_struggling_and_did_not_ask() -> None:
    allowed = plan(photo_fits=True)

    assert may_send_photo(understanding(False, False), allowed)
    assert may_send_photo(understanding(False, True), allowed)
    assert may_send_photo(understanding(True, True), allowed)
    assert not may_send_photo(understanding(True, False), allowed)


def test_the_reply_plan_can_rule_a_photo_out_whatever_the_user_asked() -> None:
    ruled_out = plan(photo_fits=False)

    assert not may_send_photo(understanding(False, False), ruled_out)
    assert not may_send_photo(understanding(True, True), ruled_out)
