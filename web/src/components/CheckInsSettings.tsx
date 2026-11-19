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
import {
  checkInFrequencyChoices,
  pausedText,
  toTimeFieldValue,
} from "@/lib/check-ins";
import { type Copy, readCopy } from "@/lib/copy";
import { useCheckIns, useMe, useSaveCheckIns } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const pauseLengths: PauseLength[] = ["day", "week", "until_resumed"];

const pauseButton =
  "min-h-11 cursor-pointer rounded-pill border border-soft bg-transparent px-[18px] text-[14px] text-text disabled:cursor-not-allowed disabled:border-line-strong disabled:text-mute";

/**
 * The Check-ins page: the on/off switch, how often, quiet hours, pausing,
 * what a check-in can be, and the recent Check-ins. It never shows when the
 * next Check-in will come; Zeph chooses the moment. A setting last changed
 * in chat or by an Admin says so under it. Every word is the Check-ins
 * tab's Copy, with the frequency names from Onboarding's.
 *
 * @param props - `copy` holds the Check-ins page's Copy slots and
 *   onboarding's frequency names.
 * @returns The page, a loading panel, or an error with Try again.
 */
export function CheckInsSettings({ copy }: { copy: Copy }) {
  const checkInsCopy = (slot: string) => readCopy(copy, `check_ins.${slot}`);
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
          text={checkInsCopy("changed_in_chat")}
        />
        <ChangedByAdminCaption
          changedAt={checkIns?.changed_by_admin[setting]}
          timeZone={timeZone}
          text={checkInsCopy("changed_by_admin")}
        />
      </>
    );
  }
  let switchLabel = checkInsCopy("switch.on");
  if (checkIns && !checkIns.available) {
    switchLabel = checkInsCopy("switch.not_available");
  } else if (checkIns && !checkIns.enabled) {
    switchLabel = checkInsCopy("switch.off");
  } else if (checkIns?.paused) {
    switchLabel = checkInsCopy("switch.paused");
  }

  return (
    <>
      <PageHero
        background="checkIns"
        eyebrow={checkInsCopy("hero.eyebrow")}
        title={checkInsCopy("hero.heading")}
        body={checkInsCopy("hero.lead")}
        actions={
          checkIns ? (
            <div className="inline-flex items-center gap-1.5 rounded-pill border border-line bg-panel pr-1 pl-[18px]">
              <span className="text-[14px] font-normal text-text">
                {switchLabel}
              </span>
              <Switch
                label={checkInsCopy("switch.label")}
                checked={checkIns.enabled}
                disabled={isSaving || !checkIns.available}
                onChange={(enabled) => changeSettings({ enabled })}
              />
            </div>
          ) : null
        }
      />

      {!isLoaded && !loadFailed ? (
        <LoadingPanel shape="card" label={checkInsCopy("loading")} />
      ) : null}

      {loadFailed ? (
        <LoadFailed
          title={checkInsCopy("load_failed.title")}
          body={checkInsCopy("load_failed.body")}
          retryLabel={checkInsCopy("load_failed.retry")}
          onRetry={() => {
            void meQuery.refetch();
            void checkInsQuery.refetch();
          }}
        />
      ) : null}

      {checkIns ? (
        <>
          {saveCheckIns.isError ? (
            <SaveFailedNote>{checkInsCopy("save_failed")}</SaveFailedNote>
          ) : null}

          {checkIns.available ? null : (
            <PausedNotice
              title={checkInsCopy("not_available.title")}
              body={checkInsCopy("not_available.body")}
            />
          )}

          {checkIns.enabled && checkIns.paused ? (
            <PausedNotice
              title={pausedText(copy, checkIns.paused_until, timeZone)}
              body={checkInsCopy("paused.body")}
              action={
                <button
                  type="button"
                  className={secondaryButton}
                  disabled={isSaving}
                  onClick={resume}
                >
                  {checkInsCopy("paused.resume")}
                </button>
              }
            />
          ) : null}
          {checkIns.available && !checkIns.enabled ? (
            <PausedNotice
              title={checkInsCopy("off.title")}
              body={checkInsCopy("off.body")}
            />
          ) : null}

          <section aria-label={checkInsCopy("settings.label")}>
            <div className="box-border rounded-card border border-line bg-panel px-6 py-1">
              <div className="flex flex-col gap-3.5 py-[18px]">
                <div>
                  <div className="text-[15px] font-normal text-text">
                    {checkInsCopy("frequency.title")}
                  </div>
                  <div className="text-[13px] text-soft">
                    {checkInsCopy("frequency.caption")}
                  </div>
                </div>
                <CheckInFrequencySegments
                  label={checkInsCopy("frequency.label")}
                  options={checkInFrequencyChoices(copy)}
                  value={checkIns.frequency}
                  disabled={isSaving}
                  onChange={(frequency) => changeSettings({ frequency })}
                />
                {changeCaption("check_in_frequency")}
              </div>
              <CheckInSettingRow
                title={checkInsCopy("quiet_hours.title")}
                caption={checkInsCopy("quiet_hours.caption")}
              >
                <QuietHoursFields
                  labels={{
                    group: checkInsCopy("quiet_hours.label"),
                    from: checkInsCopy("quiet_hours.from"),
                    until: checkInsCopy("quiet_hours.until"),
                  }}
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
                title={checkInsCopy("pause.title")}
                caption={checkInsCopy("pause.caption")}
              >
                <div className="flex flex-wrap gap-2">
                  {pauseLengths.map((length) => (
                    <button
                      key={length}
                      type="button"
                      className={pauseButton}
                      disabled={isSaving}
                      onClick={() => pause(length)}
                    >
                      {checkInsCopy(`pause.${length}`)}
                    </button>
                  ))}
                </div>
                {changeCaption("check_in_pause")}
              </CheckInSettingRow>
            </div>
            <p className="mt-3 mb-0 text-[13px] text-soft">
              {checkInsCopy("tell_zeph")}
            </p>
          </section>

          <CheckInKindsList kinds={checkIns.kinds} copy={copy} />

          <RecentCheckInsList
            checkIns={checkIns.recent}
            copy={copy}
            timeZone={timeZone}
          />
        </>
      ) : null}
    </>
  );
}
