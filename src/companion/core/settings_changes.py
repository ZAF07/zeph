from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime

from companion.core.models import ChatSetting, User


def record_where_changed(
    user: User, settings: Iterable[ChatSetting], in_chat: bool, now: datetime
) -> User:
    """Note whether settings were just changed in chat or on the Dashboard.

    A setting changed in chat is stamped with the time, so the Dashboard can
    show "Changed in chat"; one changed on the Dashboard loses its stamp.

    Args:
        user: The User whose settings changed.
        settings: The settings that changed.
        in_chat: True if the User changed them by telling the Companion.
        now: The current time.

    Returns:
        The User with their changed-in-chat stamps brought up to date.
    """
    stamps = dict(user.settings_changed_in_chat)
    for setting in settings:
        if in_chat:
            stamps[setting] = now
        else:
            stamps.pop(setting, None)
    return replace(user, settings_changed_in_chat=stamps)
