"use client";

import { secondaryButton } from "@/components/button-styles";
import { ChangedByAdminCaption } from "@/components/ChangedByAdminCaption";
import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { CheckInFrequencySegments } from "@/components/CheckInFrequencySegments";
import { CheckInKindsList } from "@/components/CheckInKindsList";
import { CheckInSettingRow } from "@/components/CheckInSettingRow";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { PageHero } from "@/components/PageHero";
import { PausedNotice } from "@/components/PausedNotice";
import { QuietHoursFields } from "@/components/QuietHoursFields";
import { RecentCheckInsList } from "@/components/RecentCheckInsList";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { Switch } from "@/components/Switch";
import type {
  ChatSetting,
  CheckInChanges,
  CheckIns,
  PauseLength,
} from "@/lib/api-client";
import { pausedText, toTimeFieldValue } from "@/lib/check-ins";
import { notAvailableText } from "@/lib/features";
import { useCheckIns, useMe, useSaveCheckIns } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const pauseChoices: { length: PauseLength; label: string }[] = [
  { length: "day", label: "For a day" },
  { length: "week", label: "For a week" },
  { length: "until_resumed", label: "Until I resume" },
];

const pauseButton =
  "min-h-11 cursor-pointer rounded-pill border border-soft bg-transparent px-[18px] text-[14px] text-text disabled:cursor-not-allowed disabled:border-line-strong disabled:text-mute";

/**
 * The Check-ins page: the on/off switch, how often, quiet hours, pausing,
 * what a check-in can be, and the recent Check-ins. It never shows when the
 * next Check-in will come; Zeph chooses the moment. A setting last changed
 * in chat or by an Admin says so under it.
 *
 * @returns The page, a loading panel, or an error with Try again.
 */
export function CheckInsSettings() {
  const apiClient = useApiClient();
  const meQuery = useMe();
  const checkInsQuery = useCheckIns();
  const saveCheckIns = useSaveCheckIns();

  const me = meQuery.data;
  const timeZone = me?.time_zone ?? undefined;
  const isLoaded = me !== undefined && checkInsQuery.data !== undefined;
  const checkIns = isLoaded ? checkInsQuery.data : null;
  const loadFailed = !isLoaded && (meQuery.isError || checkInsQuery.isError);
  const changedInChat = me?.changed_in_chat ?? {};
  const isSaving = saveCheckIns.isPending;

  function save(sendChange: () => Promise<CheckIns>) {
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

  function changeCaption(setting: ChatSetting) {
    return (
      <>
        <ChangedInChatCaption
          changedAt={changedInChat[setting]}
          timeZone={timeZone}
        />
        <ChangedByAdminCaption
          changedAt={checkIns?.changed_by_admin[setting]}
          timeZone={timeZone}
        />
      </>
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
      <PageHero
        background="checkIns"
        eyebrow="Check-ins"
        title="Check-ins"
        body="Now and then Zeph can message you first on Telegram. There's no fixed schedule: Zeph chooses the moment and the kind, and sometimes stays quiet to give you space."
        actions={
          checkIns ? (
            <div className="inline-flex items-center gap-1.5 rounded-pill border border-line bg-panel pr-1 pl-[18px]">
              <span className="text-[14px] font-normal text-text">
                {switchLabel}
              </span>
              <Switch
                label="Check-ins"
                checked={checkIns.enabled}
                disabled={isSaving || !checkIns.available}
                onChange={(enabled) => changeSettings({ enabled })}
              />
            </div>
          ) : null
        }
      />

      {!isLoaded && !loadFailed ? (
        <LoadingPanel shape="card" label="Loading Check-ins" />
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
        <>
          {saveCheckIns.isError ? (
            <SaveFailedNote>
              Couldn’t save your check-in settings. They are as you left them.
              Try again.
            </SaveFailedNote>
          ) : null}

          {checkIns.available ? null : (
            <PausedNotice
              title="Check-ins aren’t available on your account"
              body="Zeph won’t message you first. Your settings are kept."
            />
          )}

          {checkIns.enabled && checkIns.paused ? (
            <PausedNotice
              title={pausedText(checkIns.paused_until, timeZone)}
              body="Zeph won’t message first until then. Everything else stays as it is."
              action={
                <button
                  type="button"
                  className={secondaryButton}
                  disabled={isSaving}
                  onClick={resume}
                >
                  Resume now
                </button>
              }
            />
          ) : null}
          {checkIns.available && !checkIns.enabled ? (
            <PausedNotice
              title="Check-ins are off"
              body="Zeph only replies when you message it."
            />
          ) : null}

          <section aria-label="Settings">
            <div className="box-border rounded-card border border-line bg-panel px-6 py-1">
              <div className="flex flex-col gap-3.5 py-[18px]">
                <div>
                  <div className="text-[15px] font-normal text-text">
                    How often, at most
                  </div>
                  <div className="text-[13px] text-soft">
                    Zeph will often check in less than this.
                  </div>
                </div>
                <CheckInFrequencySegments
                  value={checkIns.frequency}
                  disabled={isSaving}
                  onChange={(frequency) => changeSettings({ frequency })}
                />
                {changeCaption("check_in_frequency")}
              </div>
              <CheckInSettingRow
                title="Quiet hours"
                caption="Zeph never checks in during these hours."
              >
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
                {changeCaption("quiet_hours")}
              </CheckInSettingRow>
              <CheckInSettingRow
                title="Need some quiet?"
                caption="Pause without changing anything else."
              >
                <div className="flex flex-wrap gap-2">
                  {pauseChoices.map((choice) => (
                    <button
                      key={choice.length}
                      type="button"
                      className={pauseButton}
                      disabled={isSaving}
                      onClick={() => pause(choice.length)}
                    >
                      {choice.label}
                    </button>
                  ))}
                </div>
                {changeCaption("check_in_pause")}
              </CheckInSettingRow>
            </div>
            <p className="mt-3 mb-0 text-[13px] text-soft">
              You can also just tell Zeph &quot;take a week off from
              check-ins&quot;.
            </p>
          </section>

          <CheckInKindsList kinds={checkIns.kinds} />

          <RecentCheckInsList checkIns={checkIns.recent} timeZone={timeZone} />
        </>
      ) : null}
    </>
  );
}
