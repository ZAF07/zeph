from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from companion.core.admin_users import UserNotFoundError
from companion.core.features import feature_statuses, switches_for_everyone
from companion.core.model_call_log import start_trace
from companion.core.models import (
    ModelCallTrace,
    PlatformSettings,
    TraceKind,
    UserSnapshot,
)
from companion.core.ports import Clock, Repositories
from companion.core.timing import local_now, users_today


class UserSnapshotLoader:
    """Reads User snapshots in a few queries, however many Users there are.

    The rules for whether a Feature works stay in `features.py`; the loader
    only gathers what they need and keeps the results.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the loader.

        Args:
            repositories: Where Users and Feature switches are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def load(
        self, user_id: UUID, settings: PlatformSettings, trace: ModelCallTrace
    ) -> UserSnapshot:
        """Read one User's snapshot.

        Args:
            user_id: The User.
            settings: The platform settings, read once for the reply or tick.
            trace: The Model Call Log trace the snapshot's model calls go in.

        Returns:
            Their snapshot.

        Raises:
            UserNotFoundError: If there is no such User.
        """
        snapshot = self.find(user_id, settings, trace)
        if snapshot is None:
            raise UserNotFoundError(user_id)
        return snapshot

    def find(
        self, user_id: UUID, settings: PlatformSettings, trace: ModelCallTrace
    ) -> UserSnapshot | None:
        """Read one User's snapshot, if they still exist.

        Args:
            user_id: The User.
            settings: The platform settings, read once for the reply or tick.
            trace: The Model Call Log trace the snapshot's model calls go in.

        Returns:
            Their snapshot, or None if there is no such User.
        """
        snapshots = self.load_many([user_id], settings, trace.kind)
        return replace(snapshots[0], trace=trace) if snapshots else None

    def load_many(
        self,
        user_ids: Sequence[UUID],
        settings: PlatformSettings,
        trace_kind: TraceKind,
    ) -> list[UserSnapshot]:
        """Read many Users' snapshots in three queries.

        The switches for everyone are read once and every User's own
        switches in one more query. The platform settings are read by the
        caller, once for the whole reply or tick, and shared by every snapshot.
        Each snapshot starts its own Model Call Log trace.

        Args:
            user_ids: The Users.
            settings: The platform settings, read once for the reply or tick.
            trace_kind: What each snapshot's Model Call Log trace is for.

        Returns:
            One snapshot per User found, in the order given; Users that don't
            exist are left out.
        """
        if not user_ids:
            return []
        found = self._repositories.users.get_many(user_ids)
        everyone_switches = switches_for_everyone(
            self._repositories.feature_switches.list_for_everyone()
        )
        switches_by_user = self._repositories.feature_switches.list_for_users(
            [user.id for user in found]
        )
        now = self._clock.now()
        return [
            UserSnapshot(
                user=user,
                local_now=local_now(user.time_zone, now),
                today=users_today(user.time_zone, now),
                features=tuple(
                    feature_statuses(
                        user, everyone_switches, switches_by_user.get(user.id, [])
                    )
                ),
                settings=settings,
                trace=start_trace(trace_kind),
            )
            for user in found
        ]
