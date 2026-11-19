"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { CheckInNowResults } from "@/components/CheckInNowResults";
import {
  primaryButton,
  rowActionButton,
  secondaryButton,
} from "@/components/button-styles";
import { DataTable } from "@/components/DataTable";
import { LoadFailed } from "@/components/LoadFailed";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { SearchField } from "@/components/SearchField";
import { StatusPill } from "@/components/StatusPill";
import type { TableColumn } from "@/components/TableCards";
import { TableEmpty } from "@/components/TableEmpty";
import { TableLoading } from "@/components/TableLoading";
import { TableNoMatches } from "@/components/TableNoMatches";
import { UserCheckInSettingsPanel } from "@/components/UserCheckInSettingsPanel";
import type {
  CheckInNowResultForUser,
  CheckInScheduleEntry,
} from "@/lib/api-client";
import {
  dueTimeText,
  heldBackText,
  quietHoursText,
  schedulePauseText,
} from "@/lib/check-in-schedule";
import { checkInFrequencyOptions } from "@/lib/check-ins";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const checkbox = "size-4 cursor-pointer accent-cream";

/**
 * Names a Check-in Frequency the way the User's Check-ins page does.
 *
 * @param entry - The User's row.
 * @returns The label, like "Most days".
 */
function frequencyLabel(entry: CheckInScheduleEntry): string {
  return (
    checkInFrequencyOptions.find((option) => option.value === entry.frequency)
      ?.label ?? entry.frequency
  );
}

/**
 * Says what the Schedule calls a User.
 *
 * @param entry - The User's row.
 * @returns Their name, else their email, else "This User".
 */
function displayName(entry: CheckInScheduleEntry): string {
  return entry.name ?? entry.email ?? "This User";
}

/**
 * The admin Check-in Schedule page: every User who opted in to Check-ins,
 * soonest Due Time first, with their settings, whether the Check-ins Feature
 * works for them and why a Check-in is held back right now. Never message
 * content. Searchable by name or email and paged; Edit (or clicking a row)
 * opens a panel to change that User's settings. Selected Users can be sent
 * a Check in Now, with each one's result shown. Built from the admin table
 * template.
 *
 * @param props - `initialSearch` fills the search box at the start, for
 *   links that open one User (from the Users page); empty by default.
 * @returns The filters, table and paging, or a loading, no-match, empty or
 *   error state in place of the table.
 */
export function CheckInSchedule({
  initialSearch = "",
}: {
  initialSearch?: string;
}) {
  const apiClient = useApiClient();
  const [search, setSearch] = useState(initialSearch);
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<CheckInScheduleEntry | null>(null);
  const closeEditing = useCallback(() => setEditing(null), []);
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [checkInNowOutcome, setCheckInNowOutcome] = useState<{
    results: CheckInNowResultForUser[];
    names: Record<string, string>;
  } | null>(null);
  const queryClient = useQueryClient();
  const checkInNow = useMutation({
    mutationFn: (names: Record<string, string>) =>
      apiClient.checkInNow(Object.keys(names)),
    onSuccess: (results, names) => {
      setCheckInNowOutcome({ results, names });
      setSelected({});
      void queryClient.invalidateQueries({
        queryKey: queryKeys.allCheckInSchedule,
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.allCheckInLog });
    },
  });
  const selectedCount = Object.keys(selected).length;

  const filter = { search, page };
  const scheduleQuery = useQuery({
    queryKey: queryKeys.checkInSchedule(filter),
    queryFn: () => apiClient.listCheckInSchedule(filter),
    placeholderData: keepPreviousData,
  });
  const schedule = scheduleQuery.data;
  const pageCount = schedule
    ? Math.max(1, Math.ceil(schedule.total / schedule.page_size))
    : 1;
  const pageEntries = schedule?.entries ?? [];
  const wholePageSelected =
    pageEntries.length > 0 &&
    pageEntries.every((entry) => entry.user_id in selected);

  const toggle = (entry: CheckInScheduleEntry) => {
    setSelected((current) => {
      const { [entry.user_id]: wasSelected, ...others } = current;
      return wasSelected === undefined
        ? { ...current, [entry.user_id]: displayName(entry) }
        : others;
    });
  };

  const toggleWholePage = () => {
    setSelected((current) => {
      const next = { ...current };
      for (const entry of pageEntries) {
        if (wholePageSelected) {
          delete next[entry.user_id];
        } else {
          next[entry.user_id] = displayName(entry);
        }
      }
      return next;
    });
  };

  const now = schedule?.now ?? "";
  const columns: TableColumn<CheckInScheduleEntry>[] = [
    {
      heading: "Select",
      cell: (entry) => (
        <span
          className="inline-flex"
          onClick={(event) => event.stopPropagation()}
        >
          <input
            type="checkbox"
            className={checkbox}
            aria-label={`Select ${displayName(entry)}`}
            checked={entry.user_id in selected}
            onChange={() => toggle(entry)}
          />
        </span>
      ),
    },
    {
      heading: "User",
      isMain: true,
      cell: (entry) => (
        <span className="inline-flex flex-col">
          <span>{entry.name ?? entry.email ?? "—"}</span>
          {entry.name ? (
            <span className="text-[12px] break-all text-soft">
              {entry.email}
            </span>
          ) : null}
        </span>
      ),
    },
    {
      heading: "Due Time",
      isMain: true,
      cell: (entry) => (
        <span className="inline-flex flex-col items-end gap-1 min-[900px]:items-start">
          {dueTimeText(entry.next_due_at, now, entry.time_zone ?? undefined)}
          {entry.check_in_now_waiting ? (
            <StatusPill filled={false}>Check in Now waiting</StatusPill>
          ) : null}
        </span>
      ),
    },
    { heading: "How often", cell: (entry) => frequencyLabel(entry) },
    {
      heading: "Quiet hours",
      cell: (entry) =>
        quietHoursText(entry.quiet_hours_start, entry.quiet_hours_end),
    },
    {
      heading: "Pause",
      cell: (entry) =>
        schedulePauseText(
          entry.paused,
          entry.paused_until,
          entry.time_zone ?? undefined,
        ),
    },
    {
      heading: "Check-ins",
      cell: (entry) => (
        <StatusPill filled={entry.check_ins_work}>
          {entry.check_ins_work ? "Works" : "Feature off"}
        </StatusPill>
      ),
    },
    {
      heading: "Held back now",
      cell: (entry) =>
        entry.held_back
          ? heldBackText(entry.held_back, now, entry.time_zone ?? undefined)
          : "—",
    },
    {
      heading: "Actions",
      cell: (entry) => (
        <button
          type="button"
          className={rowActionButton}
          onClick={(event) => {
            event.stopPropagation();
            setEditing(entry);
          }}
        >
          Edit
        </button>
      ),
    },
  ];

  return (
    <>
      <div className="flex flex-wrap items-center gap-2.5">
        <SearchField
          label="Search Users"
          placeholder="Search by name or email"
          value={search}
          onChange={(value) => {
            setSearch(value);
            setPage(1);
          }}
        />
        {schedule && schedule.total > 0 ? (
          <>
            <label className="inline-flex min-h-11 cursor-pointer items-center gap-2 text-[14px] text-text">
              <input
                type="checkbox"
                className={checkbox}
                checked={wholePageSelected}
                onChange={toggleWholePage}
              />
              Select everyone on this page
            </label>
            <button
              type="button"
              className={primaryButton}
              disabled={selectedCount === 0 || checkInNow.isPending}
              onClick={() => checkInNow.mutate(selected)}
            >
              {checkInNow.isPending ? "Asking…" : "Check in now"}
            </button>
            <span className="text-[13px] text-soft">
              {selectedCount === 0
                ? "Select Users to send each a Check-in on the next tick."
                : `${selectedCount} selected · goes past pause, Quiet Hours and the Feature switch`}
            </span>
          </>
        ) : null}
      </div>

      {checkInNowOutcome ? (
        <CheckInNowResults
          results={checkInNowOutcome.results}
          names={checkInNowOutcome.names}
          onDismiss={() => setCheckInNowOutcome(null)}
        />
      ) : null}

      {checkInNow.isError ? (
        <SaveFailedNote>
          Couldn’t ask for a Check in Now. Nothing was requested; try again.
        </SaveFailedNote>
      ) : null}

      {scheduleQuery.isPending ? (
        <TableLoading label="Loading the Check-in Schedule" />
      ) : null}

      {!schedule && scheduleQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Check-in Schedule"
          body="No settings were changed."
          onRetry={() => void scheduleQuery.refetch()}
        />
      ) : null}

      {schedule && schedule.total === 0 && search.trim() ? (
        <TableNoMatches />
      ) : null}

      {schedule && schedule.total === 0 && !search.trim() ? (
        <TableEmpty
          title="No one has opted in to Check-ins yet"
          body="Users appear here once they turn Check-ins on. You’ll see their Due Time and settings — never message content."
        />
      ) : null}

      {schedule && schedule.total > 0 ? (
        <>
          <DataTable
            columns={columns}
            rows={schedule.entries}
            rowKey={(entry) => entry.user_id}
            noMessageContent
            minWidthClass="min-w-[900px]"
            onRowClick={setEditing}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-[13px] text-soft">
              Page {page} of {pageCount}
            </span>
            <span className="flex gap-2">
              <button
                type="button"
                className={secondaryButton}
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous page
              </button>
              <button
                type="button"
                className={secondaryButton}
                disabled={page >= pageCount}
                onClick={() => setPage(page + 1)}
              >
                Next page
              </button>
            </span>
          </div>
        </>
      ) : null}

      {editing ? (
        <UserCheckInSettingsPanel entry={editing} onClose={closeEditing} />
      ) : null}
    </>
  );
}
