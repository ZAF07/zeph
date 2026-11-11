from dataclasses import replace
from uuid import UUID

from companion.core.models import (
    MemoryCategory,
    MemoryCategoryDetails,
    MemoryCategoryOverview,
    User,
)
from companion.core.ports import Clock, Repositories

ONBOARDING_CATEGORY_SETTINGS = (
    "onboarding_name_memory_category",
    "onboarding_reasons_memory_category",
)


class MemoryCategoryNotFoundError(LookupError):
    """Raised when no Memory Category has the given ID."""


class InvalidMemoryCategoryError(ValueError):
    """Raised when a Memory Category's details are not valid."""


class MemoryCategoryService:
    """Lets Admins add, edit, archive and restore Memory Categories.

    Categories are never deleted, because Memory Items belong to them. An
    archived category keeps its items but gets no new ones. Post-conversation
    processing and memory retrieval read the list fresh each time, so changes
    take effect straight away.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the service.

        Args:
            repositories: Where Memory Categories and settings are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def list_overviews(self) -> list[MemoryCategoryOverview]:
        """List every Memory Category with its Memory Item count, in order.

        Returns:
            The categories, archived ones included.
        """
        return self._repositories.memory_categories.list_overviews()

    def add(self, details: MemoryCategoryDetails) -> MemoryCategory:
        """Add an active Memory Category last in the list.

        Args:
            details: Its name, description and "always include".

        Returns:
            The saved category.

        Raises:
            InvalidMemoryCategoryError: If the name or description is blank,
                or another category already has the name.
        """
        checked = self._checked_details(details, editing_id=None)
        return self._repositories.memory_categories.add(checked)

    def update(
        self, admin: User, category_id: UUID, details: MemoryCategoryDetails
    ) -> MemoryCategory:
        """Change a Memory Category's name, description and "always include".

        When the category is renamed, the onboarding settings that name it
        are renamed too, so onboarding answers keep being remembered.

        Args:
            admin: The Admin making the change.
            category_id: The category's ID.
            details: Its new name, description and "always include".

        Returns:
            The saved category.

        Raises:
            MemoryCategoryNotFoundError: If there is no such category.
            InvalidMemoryCategoryError: If the name or description is blank,
                or another category already has the name.
        """
        category = self._get(category_id)
        checked = self._checked_details(details, editing_id=category_id)
        saved = self._repositories.memory_categories.update(
            replace(
                category,
                name=checked.name,
                description=checked.description,
                always_include=checked.always_include,
            )
        )
        if saved.name != category.name:
            self._rename_in_onboarding_settings(admin, category.name, saved.name)
        return saved

    def set_archived(self, category_id: UUID, archived: bool) -> MemoryCategory:
        """Archive or restore a Memory Category.

        Args:
            category_id: The category's ID.
            archived: True to archive it, False to restore it.

        Returns:
            The saved category.

        Raises:
            MemoryCategoryNotFoundError: If there is no such category.
        """
        category = self._get(category_id)
        return self._repositories.memory_categories.update(
            replace(category, archived=archived)
        )

    def _get(self, category_id: UUID) -> MemoryCategory:
        """Find a Memory Category.

        Args:
            category_id: The category's ID.

        Returns:
            The category.

        Raises:
            MemoryCategoryNotFoundError: If there is none.
        """
        category = self._repositories.memory_categories.get(category_id)
        if category is None:
            raise MemoryCategoryNotFoundError(category_id)
        return category

    def _checked_details(
        self, details: MemoryCategoryDetails, editing_id: UUID | None
    ) -> MemoryCategoryDetails:
        """Check a Memory Category's details and tidy their spacing.

        Names are compared ignoring case, because the chat models name
        categories that way.

        Args:
            details: The details an Admin entered.
            editing_id: The category being edited, whose own name is allowed;
                None when adding.

        Returns:
            The details with surrounding spaces removed.

        Raises:
            InvalidMemoryCategoryError: If the name or description is blank,
                or another category already has the name.
        """
        name = details.name.strip()
        description = details.description.strip()
        if not name:
            raise InvalidMemoryCategoryError("A Memory Category needs a name.")
        if not description:
            raise InvalidMemoryCategoryError("A Memory Category needs a description.")
        for other in self._repositories.memory_categories.list_all():
            if other.id != editing_id and other.name.lower() == name.lower():
                raise InvalidMemoryCategoryError(
                    f"There is already a category called {other.name}."
                )
        return MemoryCategoryDetails(
            name=name, description=description, always_include=details.always_include
        )

    def _rename_in_onboarding_settings(
        self, admin: User, old_name: str, new_name: str
    ) -> None:
        """Point the onboarding settings that named a category at its new name.

        Args:
            admin: The Admin who renamed it.
            old_name: The category's old name.
            new_name: Its new name.
        """
        settings = self._repositories.platform_settings
        renamed = {
            key: new_name
            for key in ONBOARDING_CATEGORY_SETTINGS
            if settings.get(key) == old_name
        }
        if renamed:
            settings.save_many(renamed, self._clock.now(), admin.id)
