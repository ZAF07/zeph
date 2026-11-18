"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { CheckInFrequencyPicker } from "@/components/CheckInFrequencyPicker";
import { QuietHoursFields } from "@/components/QuietHoursFields";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type {
  AdminCheckInChanges,
  CheckInScheduleEntry,
  PauseLength,
} from "@/lib/api-client";
import { schedulePauseText } from "@/lib/check-in-schedule";
import { toTimeFieldValue } from "@/lib/check-ins";
import { queryKeys, reloadUserPages } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const pauseChoices: { length: PauseLength; label: string }[] = [
  { length: "day", label: "For a day" },
  { length: "week", label: "For a week" },
  { length: "until_resumed", label: "Until resumed" },
];

const settingRow = "flex flex-col gap-2.5 border-t border-line px-5 py-4";

/**
 * The side panel where an Admin changes one opted-in User's own Check-in
 * settings: how often, Quiet Hours, and pausing or resuming. Each change
 * saves straight away and the User sees it marked "Changed by an Admin".
 * There is no on/off switch; stopping a User's Check-ins is the Check-ins
 * Feature switch. Escape closes the panel, unless a change is being saved.
 *
 * @param props - `entry` is the User's row on the Check-in Schedule;
 *   `onClose` closes the panel.
 * @returns The panel as a dialog.
 */
export function UserCheckInSettingsPanel({
  entry,
  onClose,
}: {
  entry: CheckInScheduleEntry;
  onClose: () => void;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [current, setCurrent] = useState(entry);
  const displayName = entry.name ?? entry.email ?? "This User";
  const timeZone = entry.time_zone ?? undefined;

  const save = useMutation({
    mutationFn: (send: () => Promise<CheckInScheduleEntry>) => send(),
    onSuccess: (saved) => {
      setCurrent(saved);
      void queryClient.invalidateQueries({
        queryKey: queryKeys.allCheckInSchedule,
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.checkIns });
      reloadUserPages(queryClient);
    },
  });
  const isSaving = save.isPending;

  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving) {
        onClose();
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isSaving, onClose]);

  function changeSettings(changes: AdminCheckInChanges) {
    save.mutate(() => apiClient.changeUserCheckIns(entry.user_id, changes));
  }

  function pause(length: PauseLength) {
    save.mutate(() => apiClient.pauseUserCheckIns(entry.user_id, length));
  }

  function resume() {
    save.mutate(() => apiClient.resumeUserCheckIns(entry.user_id));
  }

  return (
    <div className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-check-ins-heading"
        className="flex max-h-[min(90vh,720px)] w-full max-w-[640px] flex-col gap-4 overflow-y-auto rounded-panel bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 flex-col gap-1">
            <h2
              id="user-check-ins-heading"
              className="m-0 text-h3 font-semibold"
            >
              Check-in settings for {displayName}
            </h2>
            {entry.name && entry.email ? (
              <p className="m-0 break-all text-caption text-ink-muted">
                {entry.email}
              </p>
            ) : null}
          </div>
          <button
            ref={closeRef}
            type="button"
            className={compactSecondaryButton}
            disabled={isSaving}
            onClick={onClose}
          >
            Close
          </button>
        </div>
        <p className="m-0 text-caption text-ink-muted">
          These are {displayName}’s own settings. Each change saves straight
          away, and they’ll see “Changed by an Admin” until they change it back.
          To stop their Check-ins, turn the Check-ins Feature off for them on
          the Users page.
        </p>

        {save.isError ? (
          <SaveFailedNote>
            Couldn’t save that for {displayName}. Their settings are unchanged.
          </SaveFailedNote>
        ) : null}

        <div className="flex flex-col rounded-card border border-line [&>*:first-child]:border-t-0">
          <div className={settingRow}>
            <span className="font-semibold">How often, at most</span>
            <CheckInFrequencyPicker
              value={current.frequency}
              disabled={isSaving}
              onChange={(frequency) => changeSettings({ frequency })}
            />
          </div>
          <div className={settingRow}>
            <span className="font-semibold">
              Quiet hours{" "}
              <span className="font-normal text-ink-muted">
                · in their time{timeZone ? ` (${timeZone})` : ""}
              </span>
            </span>
            <QuietHoursFields
              start={toTimeFieldValue(current.quiet_hours_start)}
              end={toTimeFieldValue(current.quiet_hours_end)}
              disabled={isSaving}
              onStartChange={(start) =>
                changeSettings({ quiet_hours_start: start })
              }
              onEndChange={(end) => changeSettings({ quiet_hours_end: end })}
            />
          </div>
          <div className={settingRow}>
            <span className="font-semibold">Pause</span>
            <span className="text-caption text-ink-muted">
              {schedulePauseText(
                current.paused,
                current.paused_until,
                timeZone,
              )}
            </span>
            <div className="flex flex-wrap gap-2">
              {pauseChoices.map((choice) => (
                <button
                  key={choice.length}
                  type="button"
                  className={compactSecondaryButton}
                  disabled={isSaving}
                  onClick={() => pause(choice.length)}
                >
                  {choice.label}
                </button>
              ))}
              {current.paused ? (
                <button
                  type="button"
                  className={compactSecondaryButton}
                  disabled={isSaving}
                  onClick={resume}
                >
                  Resume
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
