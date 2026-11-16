from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime

from companion.core.models import ChangedBy, ChatSetting, User


def record_where_changed(
    user: User, settings: Iterable[ChatSetting], changed_by: ChangedBy, now: datetime
) -> User:
    """Note who changed settings: the User in chat or on the Dashboard, or an Admin.

    A setting changed in chat is stamped with the time, so the Dashboard can
    show "Changed in chat"; one changed by an Admin is stamped so it can show
    "Changed by an Admin". Each change drops the other stamp, and one the
    User makes on the Dashboard drops both.

    Args:
        user: The User whose settings changed.
        settings: The settings that changed.
        changed_by: Who changed them, and where.
        now: The current time.

    Returns:
        The User with their changed-in-chat and changed-by-an-Admin stamps
        brought up to date.
    """
    in_chat = dict(user.settings_changed_in_chat)
    by_admin = dict(user.settings_changed_by_admin)
    for setting in settings:
        in_chat.pop(setting, None)
        by_admin.pop(setting, None)
        if changed_by == ChangedBy.CHAT:
            in_chat[setting] = now
        elif changed_by == ChangedBy.ADMIN:
            by_admin[setting] = now
    return replace(
        user, settings_changed_in_chat=in_chat, settings_changed_by_admin=by_admin
    )
