"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { CheckInFrequencyPicker } from "@/components/CheckInFrequencyPicker";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { LocationFields } from "@/components/LocationFields";
import { OnboardingProgress } from "@/components/OnboardingProgress";
import { OnboardingStepFrame } from "@/components/OnboardingStepFrame";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { Switch } from "@/components/Switch";
import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";
import type { CheckInFrequency, CheckIns, Me } from "@/lib/api-client";
import {
  checkInFrequencyOptions,
  formatQuietHour,
  toTimeFieldValue,
} from "@/lib/check-ins";
import { type Copy, fillPlaceholders, readCopy } from "@/lib/copy";
import { countryFromBrowser } from "@/lib/countries";
import { paragraphs } from "@/lib/paragraphs";
import {
  useCheckIns,
  useCompleteOnboarding,
  useMe,
  usePlatformContent,
} from "@/lib/queries";
import { timeZoneFromBrowser } from "@/lib/time-zones";

const STEP_KEYS = [
  "hello",
  "intentions",
  "location",
  "check_ins",
  "memory",
  "telegram",
];
const HELLO_STEP = 0;
const INTENTIONS_STEP = 1;
const LOCATION_STEP = 2;
const CHECK_INS_STEP = 3;
const MEMORY_STEP = 4;
const TELEGRAM_STEP = 5;

const stepHeading =
  "m-0 text-[clamp(32px,4.4vw,42px)] font-normal leading-[1.1] tracking-[-0.4px] text-cream";
const stepIntro = "m-0 text-[16px] text-soft";
const stepPanel =
  "box-border flex flex-col gap-3 rounded-tile border border-line bg-panel px-5 py-[18px]";
const textFieldLabel = "flex flex-col gap-1.5";
const fieldName = "text-[14px] text-text";
const textField =
  "box-border rounded-input border border-line-strong bg-bg-deep px-3.5 text-[15px] text-text placeholder:text-mute";
const smallNote = "m-0 text-[13px] text-soft";

/** The answers being filled in, before they are saved. */
type Answers = {
  name: string;
  aiNoticeAcknowledged: boolean;
  reasons: string[];
  note: string;
  userMemoryEnabled: boolean;
  country: string;
  timeZone: string;
  checkInsEnabled: boolean;
  checkInFrequency: CheckInFrequency;
  quietHoursStart: string;
  quietHoursEnd: string;
};

/**
 * Starts the answers from what the User saved before, or from the browser.
 *
 * @param me - The signed-in User.
 * @param checkIns - Their Check-in settings, which start as the backend's
 *   defaults.
 * @returns The starting answers.
 */
function startingAnswers(me: Me, checkIns: CheckIns): Answers {
  return {
    name: me.name ?? "",
    aiNoticeAcknowledged: me.ai_notice_acknowledged_at !== null,
    reasons: me.onboarding_reasons,
    note: me.onboarding_note ?? "",
    userMemoryEnabled: me.user_memory_enabled,
    country: me.country ?? countryFromBrowser(navigator.languages) ?? "",
    timeZone: me.time_zone ?? timeZoneFromBrowser(),
    checkInsEnabled: checkIns.enabled,
    checkInFrequency: checkIns.frequency,
    quietHoursStart: toTimeFieldValue(checkIns.quiet_hours_start),
    quietHoursEnd: toTimeFieldValue(checkIns.quiet_hours_end),
  };
}

/**
 * The onboarding steps a new User goes through before Connect Telegram:
 * name and AI notice, what brings them here, country and time zone,
 * Check-ins (off by default), User Memory consent, then Telegram. Answers
 * are saved when they leave the Memory step. A User who already finished
 * onboarding goes to the Dashboard. Every word is Copy, apart from the
 * reason choices, which are a Platform Setting. The User Memory explanation
 * is Shared Copy and the Telegram card's words are Connect Telegram's Copy.
 *
 * @param props - `copy` is the website's Copy; `showAllSteps` stacks every
 *   step for the design sheet
 *   (`?design=all-steps`), each drawn ready to continue (its buttons do
 *   nothing), instead of one at a time.
 * @returns The onboarding flow.
 */
export function OnboardingFlow({
  copy,
  showAllSteps = false,
}: {
  copy: Copy;
  showAllSteps?: boolean;
}) {
  const router = useRouter();
  const meQuery = useMe();
  const contentQuery = usePlatformContent();
  const checkInsQuery = useCheckIns();
  const completeOnboarding = useCompleteOnboarding();
  const [answers, setAnswers] = useState<Answers | null>(null);
  const [step, setStep] = useState(HELLO_STEP);
  const [countryFromBrowserUsed, setCountryFromBrowserUsed] = useState(false);

  const me = meQuery.data;
  const checkIns = checkInsQuery.data;
  const content = contentQuery.data;
  const onboardingCopy = (key: string) => readCopy(copy, `onboarding.${key}`);
  const frame = {
    wordmark: readCopy(copy, "shared.wordmark"),
    homeLinkLabel: readCopy(copy, "shared.header.home_link_label"),
  };
  const stepLabels = STEP_KEYS.map((key) => onboardingCopy(`progress.${key}`));

  useEffect(() => {
    if (answers || !me || !checkIns) {
      return;
    }
    if (me.onboarding_completed_at) {
      router.replace("/");
      return;
    }
    const starting = startingAnswers(me, checkIns);
    setAnswers(starting);
    setCountryFromBrowserUsed(!me.country && starting.country !== "");
  }, [answers, me, checkIns, router]);

  const loadFailed =
    (!answers && (meQuery.isError || checkInsQuery.isError)) ||
    (!content && contentQuery.isError);

  if (loadFailed) {
    return (
      <OnboardingStepFrame {...frame}>
        <LoadFailed
          title={onboardingCopy("load_failed.title")}
          body={onboardingCopy("load_failed.body")}
          retryLabel={onboardingCopy("load_failed.retry")}
          onRetry={() => {
            void meQuery.refetch();
            void contentQuery.refetch();
            void checkInsQuery.refetch();
          }}
        />
      </OnboardingStepFrame>
    );
  }

  if (!answers || !content) {
    return (
      <OnboardingStepFrame {...frame}>
        <LoadingPanel shape="card" label={onboardingCopy("loading")} />
      </OnboardingStepFrame>
    );
  }

  function change(changes: Partial<Answers>) {
    setAnswers((current) => (current ? { ...current, ...changes } : current));
  }

  function toggleReason(reason: string) {
    if (!answers) {
      return;
    }
    const reasons = answers.reasons.includes(reason)
      ? answers.reasons.filter((picked) => picked !== reason)
      : [...answers.reasons, reason];
    change({ reasons });
  }

  function saveAndContinue() {
    if (!answers) {
      return;
    }
    completeOnboarding.mutate(
      {
        name: answers.name.trim(),
        ai_notice_acknowledged: answers.aiNoticeAcknowledged,
        onboarding_reasons: answers.reasons,
        onboarding_note: answers.note.trim() || null,
        user_memory_enabled: answers.userMemoryEnabled,
        country: answers.country,
        time_zone: answers.timeZone,
        check_ins_enabled: answers.checkInsEnabled,
        check_in_frequency: answers.checkInFrequency,
        quiet_hours_start: answers.quietHoursStart,
        quiet_hours_end: answers.quietHoursEnd,
      },
      { onSuccess: () => setStep(TELEGRAM_STEP) },
    );
  }

  const needsName = !answers.name.trim();
  const needsAcknowledgement = !answers.aiNoticeAcknowledged;
  const needsLocation = !answers.country || !answers.timeZone;

  function canLeave(stepIndex: number): boolean {
    if (completeOnboarding.isPending) {
      return false;
    }
    if (stepIndex === HELLO_STEP) {
      return !needsName && !needsAcknowledgement;
    }
    if (stepIndex === LOCATION_STEP) {
      return !needsLocation;
    }
    return true;
  }

  function next() {
    if (!canLeave(step)) {
      return;
    }
    if (step === MEMORY_STEP) {
      saveAndContinue();
      return;
    }
    setStep(step + 1);
  }

  function stepContent(stepIndex: number, isDesignSheet: boolean) {
    if (!answers || !content) {
      return null;
    }
    if (stepIndex === HELLO_STEP) {
      const showHint = !isDesignSheet && (needsName || needsAcknowledgement);
      return (
        <>
          <h1 className={stepHeading}>{onboardingCopy("hello.heading")}</h1>
          <p className={stepIntro}>{onboardingCopy("hello.intro")}</p>
          <label className={textFieldLabel}>
            <span className={fieldName}>
              {onboardingCopy("hello.name_label")}
            </span>
            <input
              className={`${textField} min-h-12`}
              type="text"
              autoComplete="given-name"
              placeholder={onboardingCopy("hello.name_hint")}
              maxLength={100}
              value={answers.name}
              onChange={(event) => change({ name: event.target.value })}
            />
          </label>
          <div className={stepPanel}>
            <p className="m-0 text-[14px] text-soft">
              {onboardingCopy("hello.ai_notice")}
            </p>
            <label className="flex min-h-11 cursor-pointer items-center gap-3 text-[14px] text-text">
              <input
                type="checkbox"
                checked={answers.aiNoticeAcknowledged}
                onChange={(event) =>
                  change({ aiNoticeAcknowledged: event.target.checked })
                }
                aria-describedby={
                  showHint ? "onboarding-continue-hint" : undefined
                }
                className="m-[3px_3px_3px_4px] size-[18px] flex-none accent-cream"
              />
              {onboardingCopy("hello.ai_notice_checkbox")}
            </label>
          </div>
          {showHint ? (
            <p id="onboarding-continue-hint" className={smallNote}>
              {needsName
                ? onboardingCopy("hello.needs_name")
                : onboardingCopy("hello.needs_tick")}
            </p>
          ) : null}
        </>
      );
    }
    if (stepIndex === INTENTIONS_STEP) {
      return (
        <>
          <h1 className={stepHeading}>
            {onboardingCopy("intentions.heading")}
          </h1>
          <p className={stepIntro}>{onboardingCopy("intentions.intro")}</p>
          <div
            role="group"
            aria-label={onboardingCopy("intentions.choices_label")}
            className="flex flex-wrap gap-2"
          >
            {content.onboarding_reason_choices.map((reason) => {
              const isPicked = answers.reasons.includes(reason);
              return (
                <button
                  key={reason}
                  type="button"
                  aria-pressed={isPicked}
                  onClick={() => toggleReason(reason)}
                  className={`min-h-11 cursor-pointer rounded-pill border px-4 text-[14px] text-text ${
                    isPicked
                      ? "border-cream bg-zeph"
                      : "border-line-strong bg-transparent"
                  }`}
                >
                  {reason}
                </button>
              );
            })}
          </div>
          <label className={textFieldLabel}>
            <span className={fieldName}>
              {onboardingCopy("intentions.note_label")}{" "}
              <span className="text-soft">
                {onboardingCopy("intentions.note_optional")}
              </span>
            </span>
            <textarea
              className={`${textField} resize-y py-3`}
              rows={3}
              maxLength={2000}
              placeholder={onboardingCopy("intentions.note_hint")}
              value={answers.note}
              onChange={(event) => change({ note: event.target.value })}
            />
          </label>
        </>
      );
    }
    if (stepIndex === LOCATION_STEP) {
      return (
        <>
          <h1 className={stepHeading}>{onboardingCopy("location.heading")}</h1>
          <LocationFields
            labels={{
              country: onboardingCopy("location.country_label"),
              chooseCountry: onboardingCopy("location.country_choose"),
              timeZone: onboardingCopy("location.time_zone_label"),
              chooseTimeZone: onboardingCopy("location.time_zone_choose"),
            }}
            country={answers.country}
            timeZone={answers.timeZone}
            onCountryChange={(country) => {
              setCountryFromBrowserUsed(false);
              change({ country });
            }}
            onTimeZoneChange={(timeZone) => change({ timeZone })}
            countryCaption={
              isDesignSheet || countryFromBrowserUsed
                ? onboardingCopy("location.from_browser")
                : undefined
            }
          />
        </>
      );
    }
    if (stepIndex === CHECK_INS_STEP) {
      return (
        <>
          <h1 className={stepHeading}>{onboardingCopy("check_ins.heading")}</h1>
          <p className={stepIntro}>{onboardingCopy("check_ins.intro")}</p>
          <div className={stepPanel}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[15px] font-normal text-text">
                  {onboardingCopy("check_ins.switch_title")}
                </div>
                <div className="text-[13px] text-soft">
                  {onboardingCopy("check_ins.switch_note")}
                </div>
              </div>
              <Switch
                label={onboardingCopy("check_ins.switch_title")}
                checked={answers.checkInsEnabled}
                onChange={(checkInsEnabled) => change({ checkInsEnabled })}
              />
            </div>
            {answers.checkInsEnabled ? (
              <>
                <CheckInFrequencyPicker
                  label={onboardingCopy("check_ins.frequency_label")}
                  options={checkInFrequencyOptions.map((option) => ({
                    value: option.value,
                    label: onboardingCopy(
                      `check_ins.frequency_${option.value}`,
                    ),
                  }))}
                  value={answers.checkInFrequency}
                  onChange={(checkInFrequency) => change({ checkInFrequency })}
                />
                <p className={smallNote}>
                  {onboardingCopy("check_ins.quiet_hours_lead")}{" "}
                  <span className="text-text">
                    {fillPlaceholders(
                      onboardingCopy("check_ins.quiet_hours_range"),
                      {
                        start: formatQuietHour(answers.quietHoursStart),
                        end: formatQuietHour(answers.quietHoursEnd),
                      },
                    )}
                  </span>
                </p>
              </>
            ) : null}
          </div>
          <p className={smallNote}>
            {onboardingCopy("check_ins.change_later")}
          </p>
        </>
      );
    }
    if (stepIndex === MEMORY_STEP) {
      return (
        <>
          <h1 className={stepHeading}>{onboardingCopy("memory.heading")}</h1>
          <div className={stepPanel}>
            <div className="flex items-center justify-between gap-4">
              <span className="text-[15px] font-normal text-text">
                {onboardingCopy("memory.switch_label")}
              </span>
              <Switch
                label={onboardingCopy("memory.switch_label")}
                checked={answers.userMemoryEnabled}
                onChange={(userMemoryEnabled) => change({ userMemoryEnabled })}
              />
            </div>
            {paragraphs(readCopy(copy, "shared.memory_explanation")).map(
              (paragraph) => (
                <p key={paragraph} className="m-0 text-[14px] text-soft">
                  {paragraph}
                </p>
              ),
            )}
          </div>
          {completeOnboarding.isError ? (
            <SaveFailedNote>
              {onboardingCopy("memory.save_failed")}
            </SaveFailedNote>
          ) : null}
        </>
      );
    }
    return (
      <>
        <h1 className={stepHeading}>{onboardingCopy("telegram.heading")}</h1>
        <p className={stepIntro}>{onboardingCopy("telegram.intro")}</p>
        <TelegramConnectionCard copy={copy} compact />
      </>
    );
  }

  function stepButtons(stepIndex: number, isDesignSheet: boolean) {
    if (stepIndex === TELEGRAM_STEP) {
      return (
        <div>
          <Link
            href="/"
            className="inline-flex min-h-11 items-center text-[14px] text-soft underline"
          >
            {onboardingCopy("telegram.skip_link")}
          </Link>
        </div>
      );
    }
    return (
      <div className="flex flex-wrap items-center gap-3 pt-2">
        {stepIndex > HELLO_STEP ? (
          <button
            type="button"
            className={secondaryButton}
            onClick={isDesignSheet ? undefined : () => setStep(step - 1)}
          >
            {onboardingCopy("buttons.back")}
          </button>
        ) : null}
        <button
          type="button"
          className={primaryButton}
          disabled={!isDesignSheet && !canLeave(stepIndex)}
          onClick={isDesignSheet ? undefined : next}
        >
          {completeOnboarding.isPending ? (
            onboardingCopy("buttons.saving")
          ) : (
            <>
              {onboardingCopy("buttons.continue")}{" "}
              <span aria-hidden="true" className="ml-2.5">
                →
              </span>
            </>
          )}
        </button>
      </div>
    );
  }

  function stepView(stepIndex: number, isDesignSheet: boolean) {
    return (
      <>
        <OnboardingProgress
          label={onboardingCopy("progress.label")}
          labels={stepLabels}
          currentStep={stepIndex}
          stepCount={fillPlaceholders(onboardingCopy("progress.step_count"), {
            step: stepIndex + 1,
            count: STEP_KEYS.length,
          })}
        />
        <div aria-hidden="true" className="h-3" />
        {stepContent(stepIndex, isDesignSheet)}
        {stepButtons(stepIndex, isDesignSheet)}
      </>
    );
  }

  if (showAllSteps) {
    return (
      <>
        {STEP_KEYS.map((stepKey, stepIndex) => (
          <OnboardingStepFrame
            {...frame}
            key={stepKey}
            hasSeparator={stepIndex > 0}
          >
            {stepView(stepIndex, true)}
          </OnboardingStepFrame>
        ))}
      </>
    );
  }

  return (
    <OnboardingStepFrame {...frame}>
      {stepView(step, false)}
    </OnboardingStepFrame>
  );
}
