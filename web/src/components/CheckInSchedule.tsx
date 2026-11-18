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
  compactSecondaryButton,
  primaryButton,
} from "@/components/button-styles";
import { EmptyState } from "@/components/EmptyState";
import { inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import { SaveFailedNote } from "@/components/SaveFailedNote";
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

const headings = [
  "User",
  "Due Time",
  "How often",
  "Quiet hours",
  "Pause",
  "Check-ins",
  "Held back now",
];

const pill =
  "inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium";

const cell = "px-[18px] py-3.5";

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
 * content. Searchable by name or email and paged; Edit opens a panel to
 * change that User's settings. Selected Users can be sent a Check in Now,
 * with each one's result shown.
 *
 * @returns The search, table and paging, or a loading, empty or error state.
 */
export function CheckInSchedule() {
  const apiClient = useApiClient();
  const [search, setSearch] = useState("");
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

  return (
    <>
      <label className="max-w-[480px]">
        <span className="sr-only">Search Users</span>
        <input
          className={inputField}
          type="search"
          placeholder="Search by name or email"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
        />
      </label>

      {scheduleQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading the Check-in Schedule"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {!schedule && scheduleQuery.isError ? (
        <LoadFailed
          title="Couldn’t load the Check-in Schedule"
          body="No settings were changed."
          onRetry={() => void scheduleQuery.refetch()}
        />
      ) : null}

      {schedule && schedule.total === 0 ? (
        <EmptyState
          title={
            search.trim()
              ? "No one matches that search"
              : "No one has opted in to Check-ins yet"
          }
          body="Users appear here once they turn Check-ins on. You’ll see their Due Time and settings — never message content."
        />
      ) : null}

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

      {schedule && schedule.total > 0 ? (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className={primaryButton}
              disabled={selectedCount === 0 || checkInNow.isPending}
              onClick={() => checkInNow.mutate(selected)}
            >
              {checkInNow.isPending ? "Asking…" : "Check in now"}
            </button>
            <span className="text-caption text-ink-muted">
              {selectedCount === 0
                ? "Select Users to send each a Check-in on the next tick."
                : `${selectedCount} selected · goes past pause, Quiet Hours and the Feature switch`}
            </span>
          </div>
          <div className="relative overflow-x-auto rounded-xl border border-line bg-white">
            <table className="w-full min-w-[980px] border-collapse text-sm">
              <caption className="border-b border-line px-4 py-2.5 text-left">
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-muted">
                  <LockIcon />
                  No message content · {schedule.total}{" "}
                  {schedule.total === 1 ? "User" : "Users"} opted in
                </span>
              </caption>
              <thead>
                <tr>
                  <th
                    scope="col"
                    className="w-0 border-b border-line bg-subtle py-3.5 pl-[18px]"
                  >
                    <input
                      type="checkbox"
                      className="size-4"
                      aria-label="Select everyone on this page"
                      checked={wholePageSelected}
                      onChange={toggleWholePage}
                    />
                  </th>
                  {headings.map((heading) => (
                    <th
                      key={heading}
                      scope="col"
                      className="whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted"
                    >
                      {heading}
                    </th>
                  ))}
                  <th scope="col" className="border-b border-line bg-subtle">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {schedule.entries.map((entry) => {
                  const timeZone = entry.time_zone ?? undefined;
                  return (
                    <tr
                      key={entry.user_id}
                      onClick={() => setEditing(entry)}
                      className="cursor-pointer border-b border-line last:border-b-0 hover:bg-hover"
                    >
                      <td
                        className="py-3.5 pl-[18px]"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          className="size-4"
                          aria-label={`Select ${displayName(entry)}`}
                          checked={entry.user_id in selected}
                          onChange={() => toggle(entry)}
                        />
                      </td>
                      <td className={`${cell} min-w-[170px]`}>
                        <span className="flex flex-col">
                          <span className="font-medium">
                            {entry.name ?? entry.email ?? "—"}
                          </span>
                          {entry.name ? (
                            <span className="break-all text-caption text-ink-muted">
                              {entry.email}
                            </span>
                          ) : null}
                        </span>
                      </td>
                      <td className={`${cell} whitespace-nowrap`}>
                        <span className="flex flex-col items-start gap-1">
                          {dueTimeText(
                            entry.next_due_at,
                            schedule.now,
                            timeZone,
                          )}
                          {entry.check_in_now_waiting ? (
                            <span
                              className={`${pill} bg-blue-tint text-blue-deep`}
                            >
                              Check in Now waiting
                            </span>
                          ) : null}
                        </span>
                      </td>
                      <td className={`${cell} whitespace-nowrap`}>
                        {frequencyLabel(entry)}
                      </td>
                      <td className={`${cell} whitespace-nowrap tabular-nums`}>
                        {quietHoursText(
                          entry.quiet_hours_start,
                          entry.quiet_hours_end,
                        )}
                      </td>
                      <td className={cell}>
                        {schedulePauseText(
                          entry.paused,
                          entry.paused_until,
                          timeZone,
                        )}
                      </td>
                      <td className={cell}>
                        <span
                          className={`${pill} ${
                            entry.check_ins_work
                              ? "bg-blue-tint text-blue-deep"
                              : "bg-yellow-tint text-yellow-deep"
                          }`}
                        >
                          {entry.check_ins_work ? "Works" : "Feature off"}
                        </span>
                      </td>
                      <td className={cell}>
                        {entry.held_back
                          ? heldBackText(
                              entry.held_back,
                              schedule.now,
                              timeZone,
                            )
                          : "—"}
                      </td>
                      <td className={cell}>
                        <button
                          type="button"
                          className={compactSecondaryButton}
                          onClick={(event) => {
                            event.stopPropagation();
                            setEditing(entry);
                          }}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-caption text-ink-muted">
              Page {page} of {pageCount}
            </span>
            <span className="flex gap-2">
              <button
                type="button"
                className={compactSecondaryButton}
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous page
              </button>
              <button
                type="button"
                className={compactSecondaryButton}
                disabled={page >= pageCount}
                onClick={() => setPage(page + 1)}
              >
                Next page
              </button>
            </span>
          </div>
          <p className="m-0 text-caption text-ink-muted">
            Changes here change the User’s own settings, by the same rules as
            their own changes. Admins can’t turn a User’s Check-ins on or off;
            to stop them, use the Check-ins Feature switch on the Users page.
          </p>
        </>
      ) : null}

      {editing ? (
        <UserCheckInSettingsPanel entry={editing} onClose={closeEditing} />
      ) : null}
    </>
  );
}
