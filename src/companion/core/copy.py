import re
from collections.abc import Mapping

from companion.core.errors import InvalidError, NotFoundError
from companion.core.models import CopySlot, CopyTab, User
from companion.core.ports import Clock, CopyRepository

PLACEHOLDER = re.compile(r"\{([^{}]*)\}")


class CopyTabNotFoundError(NotFoundError):
    """Raised when the Copy page has no tab with the given key."""

    shown_message = "No such Copy tab"


class InvalidCopyError(InvalidError):
    """Raised when some texts in a tab save are not valid; nothing is saved.

    Attributes:
        problems: What is wrong with each failing slot's text, by slot key.
    """

    shown_message = "Some texts can’t be saved. See each one."

    def __init__(self, problems: Mapping[str, str]) -> None:
        """Set up the error.

        Args:
            problems: What is wrong with each failing slot's text, by key.
        """
        super().__init__(self.shown_message)
        self.problems = dict(problems)

    def field_errors(self) -> dict[str, str]:
        """Give what is wrong per slot, to show on each slot.

        Returns:
            The reason for each failing slot, by its key.
        """
        return self.problems


def text_problem(slot: CopySlot, text: str) -> str | None:
    """Say what is wrong with a new text for a slot, if anything.

    Args:
        slot: The slot the text is for.
        text: The new text, with surrounding spaces removed.

    Returns:
        The reason it can't be saved, or None when it is fine.
    """
    if not text:
        return "This text can’t be empty."
    if len(text) > slot.max_length:
        return f"Keep it to {slot.max_length} characters or fewer."
    used = PLACEHOLDER.findall(text)
    unknown = [name for name in used if name not in slot.placeholders]
    if unknown:
        return f"{{{unknown[0]}}} isn’t a placeholder this text takes."
    missing = [name for name in slot.placeholders if name not in used]
    if missing:
        return f"Keep {{{missing[0]}}} in the text."
    return None


def group_by_tab(slots: list[CopySlot]) -> list[CopyTab]:
    """Group slots into their tabs, keeping their order.

    Args:
        slots: Every slot, by tab order and then page order.

    Returns:
        The tabs in order, each with its slots.
    """
    tabs: dict[str, CopyTab] = {}
    for slot in slots:
        tab = tabs.setdefault(
            slot.tab, CopyTab(tab=slot.tab, name=slot.tab_name, slots=[])
        )
        tab.slots.append(slot)
    return list(tabs.values())


class CopyService:
    """Serves the website's Copy and lets Admins change it one tab at a time.

    Copy is read from the store on every call, so a saved change shows on the
    next page load whichever backend process serves it.
    """

    def __init__(self, copy: CopyRepository, clock: Clock) -> None:
        """Set up the service.

        Args:
            copy: Where Copy is stored.
            clock: Tells the current time.
        """
        self._copy = copy
        self._clock = clock

    def read_all(self) -> dict[str, str]:
        """Read every slot's current text, for the website.

        Returns:
            Each slot's text by key.
        """
        return self._copy.texts()

    def copy_page(self) -> list[CopyTab]:
        """Read the Copy page for Admins.

        Returns:
            The tabs in order, each with its slots in page order.
        """
        return group_by_tab(self._copy.list_slots())

    def save_tab(
        self, admin: User, tab: str, texts: Mapping[str, str]
    ) -> list[CopyTab]:
        """Check and save one tab's changed texts, all together or not at all.

        Args:
            admin: The Admin making the change.
            tab: The key of the tab being saved.
            texts: The new text for each changed slot, by key.

        Returns:
            The Copy page after the save.

        Raises:
            CopyTabNotFoundError: If there is no such tab.
            InvalidCopyError: If a text is empty, too long, missing a
                placeholder or has an unknown one, or a slot is not on this
                tab; nothing is saved.
        """
        slots = {slot.key: slot for slot in self._copy.list_slots()}
        if not any(slot.tab == tab for slot in slots.values()):
            raise CopyTabNotFoundError(tab)
        tidied = {key: text.strip() for key, text in texts.items()}
        problems: dict[str, str] = {}
        for key, text in tidied.items():
            slot = slots.get(key)
            problem = (
                "This text isn’t on this tab."
                if slot is None or slot.tab != tab
                else text_problem(slot, text)
            )
            if problem:
                problems[key] = problem
        if problems:
            raise InvalidCopyError(problems)
        if tidied:
            self._copy.save_texts(tidied, self._clock.now(), admin.id)
        return self.copy_page()
