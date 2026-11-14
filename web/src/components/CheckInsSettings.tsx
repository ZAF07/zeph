"use client";

import { useMemo } from "react";

import { secondaryButton } from "@/components/button-styles";
import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { CheckInFrequencyPicker } from "@/components/CheckInFrequencyPicker";
import { CheckInKindsList } from "@/components/CheckInKindsList";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { QuietHoursFields } from "@/components/QuietHoursFields";
import { RecentCheckInsList } from "@/components/RecentCheckInsList";
import { SettingLabel } from "@/components/SettingLabel";
import { Switch } from "@/components/Switch";
import type { CheckInChanges, CheckIns, PauseLength } from "@/lib/api-client";
import { pausedText, toTimeFieldValue } from "@/lib/check-ins";
import { notAvailableText } from "@/lib/features";
import {
  useCheckIns,
  useMe,
  useSaveCheckIns,
  useUpdatePreferences,
} from "@/lib/queries";
import { timeZoneOptions } from "@/lib/time-zones";
import { useApiClient } from "@/lib/use-api-client";

const pauseChoices: { length: PauseLength; label: string }[] = [
  { length: "day", label: "For a day" },
  { length: "week", label: "For a week" },
  { length: "until_resumed", label: "Until I resume" },
];

const settingsRow =
  "flex flex-wrap items-center justify-between gap-x-5 gap-y-3 border-t border-line px-6 py-4";

/**
 * The Check-ins page: the on/off switch, how often, quiet hours and time
 * zone, pausing, what Zeph might reach out about, and the recent Check-ins. It never shows when the next
 * Check-in will come; Zeph chooses the moment.
 *
 * @returns The page, a loading block, or an error with Try again.
 */
export function CheckInsSettings() {
  const apiClient = useApiClient();
  const meQuery = useMe();
  const checkInsQuery = useCheckIns();
  const saveCheckIns = useSaveCheckIns();
  const updatePreferences = useUpdatePreferences();

  const me = meQuery.data;
  const timeZone = me?.time_zone ?? null;
  const timeZones = useMemo(() => timeZoneOptions(timeZone), [timeZone]);
  const isLoaded = me !== undefined && checkInsQuery.data !== undefined;
  const checkIns = isLoaded ? checkInsQuery.data : null;
  const loadFailed = !isLoaded && (meQuery.isError || checkInsQuery.isError);
  const changedInChat = me?.changed_in_chat ?? {};
  const isSaving = saveCheckIns.isPending || updatePreferences.isPending;
  const saveFailed = saveCheckIns.isError || updatePreferences.isError;

  function save(sendChange: () => Promise<CheckIns>) {
    updatePreferences.reset();
    saveCheckIns.mutate(sendChange);
  }

  function changeSettings(changes: CheckInChanges) {
    save(() => apiClient.updateCheckIns(changes));
  }

  function pause(length: PauseLength) {
    save(() => apiClient.pauseCheckIns(length));
  }

  function resume() {
    save(() => apiClient.resumeCheckIns());
  }

  function changeTimeZone(timeZone: string) {
    saveCheckIns.reset();
    updatePreferences.mutate({ time_zone: timeZone });
  }

  function chatCaption(changedAt: string | undefined) {
    return (
      <ChangedInChatCaption
        changedAt={changedAt}
        timeZone={timeZone ?? undefined}
      />
    );
  }
  let switchLabel = "Check-ins on";
  if (checkIns && !checkIns.available) {
    switchLabel = notAvailableText;
  } else if (checkIns && !checkIns.enabled) {
    switchLabel = "Check-ins off";
  } else if (checkIns?.paused) {
    switchLabel = "Paused";
  }

  return (
    <>
      <header className="flex flex-wrap items-start justify-between gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="m-0 text-h1 font-normal">Check-ins</h1>
          <p className="m-0 max-w-[40em] text-body text-ink-soft">
            Now and then Zeph can message you first on Telegram. There’s no
            fixed schedule: Zeph chooses the moment and the kind, and sometimes
            stays quiet to give you space.
          </p>
        </div>
        {checkIns ? (
          <div className="flex items-center gap-3 rounded-full border border-line bg-white py-1.5 pr-1.5 pl-[18px]">
            <span className="text-sm font-medium">{switchLabel}</span>
            <Switch
              label="Check-ins"
              checked={checkIns.enabled}
              disabled={isSaving || !checkIns.available}
              onChange={(enabled) => changeSettings({ enabled })}
            />
          </div>
        ) : null}
      </header>

      {!isLoaded && !loadFailed ? (
        <div
          aria-busy="true"
          aria-label="Loading Check-ins"
          className="flex flex-col gap-5"
        >
          <span className="block h-[260px] rounded-card bg-subtle" />
          <span className="block h-[180px] rounded-card bg-subtle" />
        </div>
      ) : null}

      {loadFailed ? (
        <LoadFailed
          title="We couldn’t load your Check-in settings"
          body="Your settings haven’t changed. Try again in a moment."
          onRetry={() => {
            void meQuery.refetch();
            void checkInsQuery.refetch();
          }}
        />
      ) : null}

      {checkIns ? (
        <div className="flex flex-col gap-9">
          {saveFailed ? (
            <p
              role="alert"
              className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3 text-sm text-danger-deep"
            >
              We couldn’t save that. Please try again.
            </p>
          ) : null}

          {checkIns.available ? null : (
            <p
              role="status"
              className="m-0 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
            >
              Check-ins aren’t available on your account, so Zeph won’t message
              you first. Your settings are kept.
            </p>
          )}

          {checkIns.enabled && checkIns.paused ? (
            <div
              role="status"
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
            >
              <span>
                {pausedText(checkIns.paused_until, timeZone ?? undefined)}
              </span>
              <button
                type="button"
                className={`${secondaryButton} bg-white`}
                disabled={isSaving}
                onClick={resume}
              >
                Resume now
              </button>
            </div>
          ) : null}
          {checkIns.available && !checkIns.enabled ? (
            <p
              role="status"
              className="m-0 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
            >
              Check-ins are off. Zeph only replies when you message it.
            </p>
          ) : null}

          <section
            aria-labelledby="check-in-settings-heading"
            className="flex flex-col rounded-card border border-line bg-white"
          >
            <h2
              id="check-in-settings-heading"
              className="m-0 px-6 pt-5 pb-3 text-[17px] font-semibold"
            >
              Settings
            </h2>
            <div className={`${settingsRow} items-start`}>
              <SettingLabel
                title="How often, at most"
                caption="Zeph will often check in less than this."
                note={chatCaption(changedInChat.check_in_frequency)}
              />
              <CheckInFrequencyPicker
                value={checkIns.frequency}
                disabled={isSaving}
                onChange={(frequency) => changeSettings({ frequency })}
              />
            </div>
            <div className={`${settingsRow} items-start`}>
              <SettingLabel
                title="Quiet hours"
                caption="Zeph never checks in during these hours."
                note={chatCaption(changedInChat.quiet_hours)}
              />
              <div className="flex flex-[2_1_480px] flex-col gap-3">
                <QuietHoursFields
                  start={toTimeFieldValue(checkIns.quiet_hours_start)}
                  end={toTimeFieldValue(checkIns.quiet_hours_end)}
                  disabled={isSaving}
                  onStartChange={(start) =>
                    changeSettings({ quiet_hours_start: start })
                  }
                  onEndChange={(end) =>
                    changeSettings({ quiet_hours_end: end })
                  }
                />
                <label className={fieldLabel}>
                  Time zone
                  <select
                    className={inputField}
                    disabled={isSaving}
                    value={timeZone ?? ""}
                    onChange={(event) => changeTimeZone(event.target.value)}
                  >
                    {timeZones.map((option) => (
                      <option key={option.name} value={option.name}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {chatCaption(changedInChat.time_zone)}
                </label>
              </div>
            </div>
            <div className={settingsRow}>
              <SettingLabel
                title="Need some quiet?"
                caption="Pause without changing anything else."
                note={chatCaption(changedInChat.check_in_pause)}
              />
              <div className="flex flex-wrap gap-2">
                {pauseChoices.map((choice) => (
                  <button
                    key={choice.length}
                    type="button"
                    className={secondaryButton}
                    disabled={isSaving}
                    onClick={() => pause(choice.length)}
                  >
                    {choice.label}
                  </button>
                ))}
              </div>
            </div>
            <p className="m-0 px-6 pb-5 text-caption text-blue">
              You can also just tell Zeph “take a week off from check-ins” or
              “no messages after 9pm”.
            </p>
          </section>

          <CheckInKindsList kinds={checkIns.kinds} />

          <RecentCheckInsList
            checkIns={checkIns.recent}
            timeZone={timeZone ?? undefined}
          />
        </div>
      ) : null}
    </>
  );
}
