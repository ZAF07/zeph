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
import { formatQuietHour, toTimeFieldValue } from "@/lib/check-ins";
import { countryFromBrowser } from "@/lib/countries";
import { paragraphs } from "@/lib/paragraphs";
import {
  useCheckIns,
  useCompleteOnboarding,
  useMe,
  usePlatformContent,
} from "@/lib/queries";
import { timeZoneFromBrowser } from "@/lib/time-zones";

const STEP_LABELS = [
  "Hello",
  "Intentions",
  "Location",
  "Check-ins",
  "Memory",
  "Telegram",
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
 * onboarding goes to the Dashboard.
 *
 * @param props - `showAllSteps` stacks every step for the design sheet
 *   (`?design=all-steps`), each drawn ready to continue (its buttons do
 *   nothing), instead of one at a time.
 * @returns The onboarding flow.
 */
export function OnboardingFlow({
  showAllSteps = false,
}: {
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
      <OnboardingStepFrame>
        <LoadFailed
          title="We couldn’t load this"
          body="Something went wrong on our side. Please try again in a moment."
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
      <OnboardingStepFrame>
        <LoadingPanel shape="card" label="Loading onboarding" />
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
          <h1 className={stepHeading}>Hello. I’m Zeph.</h1>
          <p className={stepIntro}>
            I’m an AI companion for reflection: a place to think out loud,
            notice what matters, and practise living by it.
          </p>
          <label className={textFieldLabel}>
            <span className={fieldName}>What should I call you?</span>
            <input
              className={`${textField} min-h-12`}
              type="text"
              autoComplete="given-name"
              placeholder="First name or nickname"
              maxLength={100}
              value={answers.name}
              onChange={(event) => change({ name: event.target.value })}
            />
          </label>
          <div className={stepPanel}>
            <p className="m-0 text-[14px] text-soft">{content.ai_notice}</p>
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
              I understand Zeph is an AI and not professional care
            </label>
          </div>
          {showHint ? (
            <p id="onboarding-continue-hint" className={smallNote}>
              {needsName
                ? "Tell me what to call you to continue."
                : "Tick the box above to continue."}
            </p>
          ) : null}
        </>
      );
    }
    if (stepIndex === INTENTIONS_STEP) {
      return (
        <>
          <h1 className={stepHeading}>What brings you here?</h1>
          <p className={stepIntro}>
            Choose any that feel true right now. This shapes where we start, not
            where we end up.
          </p>
          <div
            role="group"
            aria-label="What brings you here"
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
              In your own words <span className="text-soft">(optional)</span>
            </span>
            <textarea
              className={`${textField} resize-y py-3`}
              rows={3}
              maxLength={2000}
              placeholder="e.g. I’ve been running on autopilot since starting a new job and want to feel more like myself."
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
          <h1 className={stepHeading}>Where are you?</h1>
          <LocationFields
            country={answers.country}
            timeZone={answers.timeZone}
            onCountryChange={(country) => {
              setCountryFromBrowserUsed(false);
              change({ country });
            }}
            onTimeZoneChange={(timeZone) => change({ timeZone })}
            countryCaption={
              isDesignSheet || countryFromBrowserUsed
                ? "Filled in from your browser"
                : undefined
            }
          />
        </>
      );
    }
    if (stepIndex === CHECK_INS_STEP) {
      return (
        <>
          <h1 className={stepHeading}>Should I check in?</h1>
          <p className={stepIntro}>
            Now and then I can message you first on Telegram: a hello to see how
            you are. I choose the moment, and sometimes I’ll stay quiet to give
            you space.
          </p>
          <div className={stepPanel}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-[15px] font-normal text-text">
                  Check-ins
                </div>
                <div className="text-[13px] text-soft">
                  Off unless you turn them on
                </div>
              </div>
              <Switch
                label="Check-ins"
                checked={answers.checkInsEnabled}
                onChange={(checkInsEnabled) => change({ checkInsEnabled })}
              />
            </div>
            {answers.checkInsEnabled ? (
              <>
                <CheckInFrequencyPicker
                  value={answers.checkInFrequency}
                  onChange={(checkInFrequency) => change({ checkInFrequency })}
                />
                <p className={smallNote}>
                  Never in your quiet hours, in your time zone:{" "}
                  <span className="text-text">
                    {formatQuietHour(answers.quietHoursStart)} to{" "}
                    {formatQuietHour(answers.quietHoursEnd)}
                  </span>
                </p>
              </>
            ) : null}
          </div>
          <p className={smallNote}>
            You can change this any time on your Check-ins page.
          </p>
        </>
      );
    }
    if (stepIndex === MEMORY_STEP) {
      return (
        <>
          <h1 className={stepHeading}>Can I remember things?</h1>
          <div className={stepPanel}>
            <div className="flex items-center justify-between gap-4">
              <span className="text-[15px] font-normal text-text">
                Remember meaningful details
              </span>
              <Switch
                label="Remember meaningful details"
                checked={answers.userMemoryEnabled}
                onChange={(userMemoryEnabled) => change({ userMemoryEnabled })}
              />
            </div>
            {paragraphs(content.user_memory_explanation).map((paragraph) => (
              <p key={paragraph} className="m-0 text-[14px] text-soft">
                {paragraph}
              </p>
            ))}
          </div>
          {completeOnboarding.isError ? (
            <SaveFailedNote>
              We couldn’t save your answers. Please try again.
            </SaveFailedNote>
          ) : null}
        </>
      );
    }
    return (
      <>
        <h1 className={stepHeading}>Let’s meet on Telegram.</h1>
        <p className={stepIntro}>
          That’s where we’ll talk. Linking takes one tap.
        </p>
        <TelegramConnectionCard compact />
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
            Skip for now
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
            Back
          </button>
        ) : null}
        <button
          type="button"
          className={primaryButton}
          disabled={!isDesignSheet && !canLeave(stepIndex)}
          onClick={isDesignSheet ? undefined : next}
        >
          {completeOnboarding.isPending ? (
            "Saving…"
          ) : (
            <>
              Continue{" "}
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
        <OnboardingProgress labels={STEP_LABELS} currentStep={stepIndex} />
        <div aria-hidden="true" className="h-3" />
        {stepContent(stepIndex, isDesignSheet)}
        {stepButtons(stepIndex, isDesignSheet)}
      </>
    );
  }

  if (showAllSteps) {
    return (
      <>
        {STEP_LABELS.map((label, stepIndex) => (
          <OnboardingStepFrame key={label} hasSeparator={stepIndex > 0}>
            {stepView(stepIndex, true)}
          </OnboardingStepFrame>
        ))}
      </>
    );
  }

  return <OnboardingStepFrame>{stepView(step, false)}</OnboardingStepFrame>;
}
