"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { CheckInFrequencyPicker } from "@/components/CheckInFrequencyPicker";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { QuietHoursFields } from "@/components/QuietHoursFields";
import { RecentCheckInsList } from "@/components/RecentCheckInsList";
import { SettingLabel } from "@/components/SettingLabel";
import { Switch } from "@/components/Switch";
import type {
  CheckInChanges,
  CheckIns,
  Me,
  PauseLength,
} from "@/lib/api-client";
import { pausedText, toTimeFieldValue } from "@/lib/check-ins";
import { timeZoneOptions } from "@/lib/time-zones";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; me: Me; checkIns: CheckIns };

const pauseChoices: { length: PauseLength; label: string }[] = [
  { length: "day", label: "For a day" },
  { length: "week", label: "For a week" },
  { length: "until_resumed", label: "Until I resume" },
];

const settingsRow =
  "flex flex-wrap items-center justify-between gap-x-5 gap-y-3 border-t border-line px-6 py-4";

/**
 * The Check-ins page: the on/off switch, how often, quiet hours and time
 * zone, pausing, and the recent Check-ins. It never shows when the next
 * Check-in will come; Zeph chooses the moment.
 *
 * @returns The page, a loading block, or an error with Try again.
 */
export function CheckInsSettings() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [isSaving, setIsSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const [me, checkIns] = await Promise.all([
        apiClient.getMe(),
        apiClient.getCheckIns(),
      ]);
      setState({ kind: "loaded", me, checkIns });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  const timeZone = state.kind === "loaded" ? state.me.time_zone : null;
  const timeZones = useMemo(() => timeZoneOptions(timeZone), [timeZone]);

  async function save(
    change: () => Promise<{ me: Me } | { checkIns: CheckIns }>,
  ) {
    setIsSaving(true);
    setSaveFailed(false);
    try {
      const saved = await change();
      setState((current) =>
        current.kind === "loaded" ? { ...current, ...saved } : current,
      );
    } catch {
      setSaveFailed(true);
    } finally {
      setIsSaving(false);
    }
  }

  function changeSettings(changes: CheckInChanges) {
    void save(async () => ({
      checkIns: await apiClient.updateCheckIns(changes),
    }));
  }

  function pause(length: PauseLength) {
    void save(async () => ({
      checkIns: await apiClient.pauseCheckIns(length),
    }));
  }

  function resume() {
    void save(async () => ({ checkIns: await apiClient.resumeCheckIns() }));
  }

  function changeTimeZone(timeZone: string) {
    void save(async () => ({
      me: await apiClient.updatePreferences({ time_zone: timeZone }),
    }));
  }

  const checkIns = state.kind === "loaded" ? state.checkIns : null;
  let switchLabel = "Check-ins on";
  if (checkIns && !checkIns.enabled) {
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
            fixed schedule: Zeph chooses the moment, and sometimes stays quiet
            to give you space.
          </p>
        </div>
        {checkIns ? (
          <div className="flex items-center gap-3 rounded-full border border-line bg-white py-1.5 pr-1.5 pl-[18px]">
            <span className="text-sm font-medium">{switchLabel}</span>
            <Switch
              label="Check-ins"
              checked={checkIns.enabled}
              disabled={isSaving}
              onChange={(enabled) => changeSettings({ enabled })}
            />
          </div>
        ) : null}
      </header>

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading Check-ins"
          className="flex flex-col gap-5"
        >
          <span className="block h-[260px] rounded-card bg-subtle" />
          <span className="block h-[180px] rounded-card bg-subtle" />
        </div>
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="We couldn’t load your Check-in settings"
          body="Your settings haven’t changed. Try again in a moment."
          onRetry={() => void load()}
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
          {!checkIns.enabled ? (
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
              />
              <CheckInFrequencyPicker
                value={checkIns.frequency}
                disabled={isSaving}
                onChange={(frequency) => changeSettings({ frequency })}
              />
            </div>
            <div className={`${settingsRow} items-end`}>
              <SettingLabel
                title="Quiet hours"
                caption="Zeph never checks in during these hours."
              />
              <div className="flex flex-[1_1_360px] flex-wrap gap-3">
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
                <label className={`${fieldLabel} flex-[2_1_180px]`}>
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
                </label>
              </div>
            </div>
            <div className={settingsRow}>
              <SettingLabel
                title="Need some quiet?"
                caption="Pause without changing anything else."
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
          </section>

          <RecentCheckInsList
            checkIns={checkIns.recent}
            timeZone={timeZone ?? undefined}
          />
        </div>
      ) : null}
    </>
  );
}
