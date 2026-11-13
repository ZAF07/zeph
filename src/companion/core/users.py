import re
from dataclasses import replace
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from companion.core.check_ins import CheckInService
from companion.core.features import FeatureService
from companion.core.models import (
    AccountIdentity,
    ChatSetting,
    Feature,
    OnboardingAnswers,
    PreferenceChanges,
    User,
    UserRole,
)
from companion.core.ports import Clock, UserRepository
from companion.core.settings_changes import record_where_changed
from companion.core.user_memory import UserMemoryService

COUNTRY_CODE_PATTERN = re.compile(r"[A-Z]{2}")
MAX_NAME_LENGTH = 100


class InvalidProfileError(ValueError):
    """Raised when onboarding answers or preferences are not acceptable."""


def clean_name(name: str) -> str:
    """Check and tidy the name the Companion should use.

    Args:
        name: The name as typed.

    Returns:
        The name without surrounding spaces.

    Raises:
        InvalidProfileError: If the name is empty or too long.
    """
    cleaned = name.strip()
    if not cleaned:
        raise InvalidProfileError("Name is required.")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise InvalidProfileError(f"Name must be at most {MAX_NAME_LENGTH} characters.")
    return cleaned


def check_country(country: str) -> str:
    """Check that a country is a two-letter code like "SG".

    Args:
        country: The country code.

    Returns:
        The country code.

    Raises:
        InvalidProfileError: If it is not two capital letters.
    """
    if not COUNTRY_CODE_PATTERN.fullmatch(country):
        raise InvalidProfileError("Country must be a two-letter code.")
    return country


def check_time_zone(time_zone: str) -> str:
    """Check that a time zone is a known IANA name like "Asia/Singapore".

    Args:
        time_zone: The time zone name.

    Returns:
        The time zone name.

    Raises:
        InvalidProfileError: If the time zone is not known.
    """
    try:
        ZoneInfo(time_zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise InvalidProfileError("Time zone is not recognised.") from error
    return time_zone


class UserService:
    """Finds the User behind a Dashboard account and keeps their profile."""

    def __init__(
        self,
        users: UserRepository,
        features: FeatureService,
        user_memory: UserMemoryService,
        check_ins: CheckInService,
        clock: Clock,
        initial_admin_emails: frozenset[str] = frozenset(),
    ) -> None:
        """Set up the service.

        Args:
            users: Where Users are stored.
            features: Says whether the Admin side allows User Memory.
            user_memory: Saves onboarding answers as Memory Items.
            check_ins: Works out the Check-in settings onboarding chooses.
            clock: Tells the current time.
            initial_admin_emails: Emails, in lower case, whose accounts become
                Admins on first sign-in.
        """
        self._users = users
        self._features = features
        self._user_memory = user_memory
        self._check_ins = check_ins
        self._clock = clock
        self._initial_admin_emails = initial_admin_emails

    def get_or_create(self, identity: AccountIdentity) -> User:
        """Return the User for an account, creating them if they are new.

        A new User whose email is an initial Admin email becomes an Admin. So
        an account made before its email was listed still gets in, a listed
        existing User also becomes an Admin while the platform has none.

        Args:
            identity: The verified account identity.

        Returns:
            The User keyed by the account's auth ID.
        """
        existing = self._users.get_by_auth_id(identity.auth_id)
        if existing is not None:
            should_bootstrap = (
                existing.role == UserRole.USER
                and self._is_initial_admin_email(identity.email)
                and self._users.count_admins() == 0
            )
            if should_bootstrap:
                return self._users.promote_to_admin(existing.id)
            return existing
        new_user = User(
            id=uuid4(),
            auth_id=identity.auth_id,
            email=identity.email,
            created_at=self._clock.now(),
            role=UserRole.ADMIN
            if self._is_initial_admin_email(identity.email)
            else UserRole.USER,
        )
        return self._users.add(new_user)

    def _is_initial_admin_email(self, email: str | None) -> bool:
        """Tell whether an email is one of the initial Admin emails.

        Args:
            email: The account's email, if known.

        Returns:
            True if it is listed, ignoring case.
        """
        return email is not None and email.lower() in self._initial_admin_emails

    def complete_onboarding(self, user: User, answers: OnboardingAnswers) -> User:
        """Save a User's onboarding answers and mark onboarding done.

        Answering again updates the answers but keeps the first completion time.
        The Check-in choices are saved with the rest. With User Memory on, the
        name and "What brings you here?" answers are also saved as Memory
        Items.

        Args:
            user: The User onboarding.
            answers: What they told the Dashboard.

        Returns:
            The saved User.

        Raises:
            InvalidProfileError: If the AI notice was not acknowledged or an
                answer is not acceptable.
        """
        if not answers.ai_notice_acknowledged:
            raise InvalidProfileError("The AI notice must be acknowledged.")
        now = self._clock.now()
        note = (answers.onboarding_note or "").strip() or None
        onboarded = replace(
            user,
            name=clean_name(answers.name),
            onboarding_reasons=answers.onboarding_reasons,
            onboarding_note=note,
            user_memory_enabled=answers.user_memory_enabled,
            country=check_country(answers.country),
            time_zone=check_time_zone(answers.time_zone),
            ai_notice_acknowledged_at=user.ai_notice_acknowledged_at or now,
            onboarding_completed_at=user.onboarding_completed_at or now,
            check_ins=self._check_ins.settings_after(user.check_ins, answers.check_ins),
        )
        saved = self._users.update(onboarded)
        self._user_memory.remember_onboarding(saved)
        return saved

    def update_preferences(
        self, user: User, changes: PreferenceChanges, in_chat: bool = False
    ) -> User:
        """Change a User's name, User Memory setting, country or time zone.

        Only the User Memory setting and time zone are marked as changed in
        chat or on the Dashboard, and only when their value really changes.

        Args:
            user: The User making the change.
            changes: The preferences to change; None leaves one as it is.
            in_chat: True if the User asked for it in chat, not on the
                Dashboard.

        Returns:
            The saved User.

        Raises:
            InvalidProfileError: If a new value is not acceptable.
            FeatureNotAvailableError: If it turns User Memory on or off while
                the Admin side has it off; nothing is changed.
        """
        changed = []
        if changes.user_memory_enabled not in (None, user.user_memory_enabled):
            self._features.require_available(user.id, Feature.USER_MEMORY)
            changed.append(ChatSetting.USER_MEMORY)
        if changes.time_zone not in (None, user.time_zone):
            changed.append(ChatSetting.TIME_ZONE)
        updated = replace(
            record_where_changed(user, changed, in_chat, self._clock.now()),
            name=clean_name(changes.name) if changes.name is not None else user.name,
            user_memory_enabled=(
                changes.user_memory_enabled
                if changes.user_memory_enabled is not None
                else user.user_memory_enabled
            ),
            country=(
                check_country(changes.country)
                if changes.country is not None
                else user.country
            ),
            time_zone=(
                check_time_zone(changes.time_zone)
                if changes.time_zone is not None
                else user.time_zone
            ),
        )
        return self._users.update(updated)
