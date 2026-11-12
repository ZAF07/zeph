"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  primaryButton,
  quietButton,
  secondaryButton,
} from "@/components/button-styles";
import { CheckInFrequencyPicker } from "@/components/CheckInFrequencyPicker";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LocationFields } from "@/components/LocationFields";
import { OnboardingProgress } from "@/components/OnboardingProgress";
import { QuietHoursFields } from "@/components/QuietHoursFields";
import { Switch } from "@/components/Switch";
import { TelegramConnectionCard } from "@/components/TelegramConnectionCard";
import type { CheckInFrequency, Me, PlatformContent } from "@/lib/api-client";
import { countryFromBrowser } from "@/lib/countries";
import { paragraphs } from "@/lib/paragraphs";
import { timeZoneFromBrowser, timeZoneLabel } from "@/lib/time-zones";
import { useApiClient } from "@/lib/use-api-client";

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
  "m-0 text-[clamp(34px,5vw,44px)] font-normal leading-[1.08] tracking-[-0.035em]";

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

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; content: PlatformContent };

/**
 * Starts the answers from what the User saved before, or from the browser.
 *
 * @param me - The signed-in User.
 * @returns The starting answers.
 */
function startingAnswers(me: Me): Answers {
  return {
    name: me.name ?? "",
    aiNoticeAcknowledged: me.ai_notice_acknowledged_at !== null,
    reasons: me.onboarding_reasons,
    note: me.onboarding_note ?? "",
    userMemoryEnabled: me.user_memory_enabled,
    country: me.country ?? countryFromBrowser(navigator.languages) ?? "",
    timeZone: me.time_zone ?? timeZoneFromBrowser(),
    checkInsEnabled: false,
    checkInFrequency: "few_times_a_week",
    quietHoursStart: "22:00",
    quietHoursEnd: "07:30",
  };
}

/**
 * The onboarding steps a new User goes through before Connect Telegram:
 * name and AI notice, what brings them here, country and time zone,
 * Check-ins (off by default), User Memory consent, then Telegram. Answers are saved when they leave the
 * Memory step. A User who already finished onboarding goes to the Dashboard.
 *
 * @returns The onboarding flow.
 */
export function OnboardingFlow() {
  const apiClient = useApiClient();
  const router = useRouter();
  const [loadState, setLoadState] = useState<LoadState>({ kind: "loading" });
  const [answers, setAnswers] = useState<Answers | null>(null);
  const [step, setStep] = useState(HELLO_STEP);
  const [countryFromBrowserUsed, setCountryFromBrowserUsed] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);

  const load = useCallback(async () => {
    setLoadState({ kind: "loading" });
    try {
      const [me, content] = await Promise.all([
        apiClient.getMe(),
        apiClient.getPlatformContent(),
      ]);
      if (me.onboarding_completed_at) {
        router.replace("/");
        return;
      }
      const starting = startingAnswers(me);
      setAnswers(starting);
      setCountryFromBrowserUsed(!me.country && starting.country !== "");
      setLoadState({ kind: "loaded", content });
    } catch {
      setLoadState({ kind: "failed" });
    }
  }, [apiClient, router]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loadState.kind === "failed") {
    return (
      <div
        role="alert"
        className="flex flex-col gap-3.5 rounded-card border border-danger-line bg-danger-tint p-7"
      >
        <p className="m-0 text-[17px] font-semibold text-danger-deep">
          We couldn’t load this
        </p>
        <p className="m-0 text-[15px] text-ink-soft">
          Something went wrong on our side. Please try again in a moment.
        </p>
        <button
          type="button"
          className={`${secondaryButton} self-start`}
          onClick={() => void load()}
        >
          Try again
        </button>
      </div>
    );
  }

  if (loadState.kind === "loading" || !answers) {
    return (
      <div
        aria-busy="true"
        className="h-[360px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const { content } = loadState;

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

  async function saveAndContinue() {
    if (!answers) {
      return;
    }
    setIsSaving(true);
    setSaveFailed(false);
    try {
      await apiClient.completeOnboarding({
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
      });
      setStep(TELEGRAM_STEP);
    } catch {
      setSaveFailed(true);
    } finally {
      setIsSaving(false);
    }
  }

  const needsName = step === HELLO_STEP && !answers.name.trim();
  const needsAcknowledgement =
    step === HELLO_STEP && !answers.aiNoticeAcknowledged;
  const needsLocation =
    step === LOCATION_STEP && (!answers.country || !answers.timeZone);
  const canContinue =
    !needsName && !needsAcknowledgement && !needsLocation && !isSaving;

  function next() {
    if (!canContinue) {
      return;
    }
    if (step === MEMORY_STEP) {
      void saveAndContinue();
      return;
    }
    setStep(step + 1);
  }

  return (
    <div className="flex flex-col gap-8">
      <OnboardingProgress labels={STEP_LABELS} currentStep={step} />

      {step === HELLO_STEP ? (
        <section className="flex flex-col gap-7">
          <div className="flex flex-col gap-3">
            <h1 className={stepHeading}>Hello. I’m Zeph.</h1>
            <p className="m-0 text-[17px] text-ink-soft">
              I’m an AI companion for reflection — a place to think out loud,
              notice what matters, and practise living by it.
            </p>
          </div>
          <label className={fieldLabel}>
            What should I call you?
            <input
              className={inputField}
              type="text"
              autoComplete="given-name"
              placeholder="First name or nickname"
              maxLength={100}
              value={answers.name}
              onChange={(event) => change({ name: event.target.value })}
            />
          </label>
          <div className="flex flex-col gap-3.5 rounded-panel bg-yellow-tint p-5">
            <p className="m-0 text-[15px] text-yellow-deep">
              {content.ai_notice}
            </p>
            <label className="flex min-h-11 cursor-pointer items-center gap-3 text-[15px] font-medium">
              <input
                type="checkbox"
                checked={answers.aiNoticeAcknowledged}
                onChange={(event) =>
                  change({ aiNoticeAcknowledged: event.target.checked })
                }
                aria-describedby="onboarding-continue-hint"
                className="size-[22px] flex-none accent-blue"
              />
              I understand Zeph is an AI and not professional care
            </label>
          </div>
          {needsName || needsAcknowledgement ? (
            <p
              id="onboarding-continue-hint"
              className="m-0 text-caption text-ink-muted"
            >
              {needsName
                ? "Tell me what to call you to continue."
                : "Tick the box above to continue."}
            </p>
          ) : null}
        </section>
      ) : null}

      {step === INTENTIONS_STEP ? (
        <section className="flex flex-col gap-7">
          <div className="flex flex-col gap-3">
            <h1 className={stepHeading}>What brings you here?</h1>
            <p className="m-0 text-[17px] text-ink-soft">
              Choose any that feel true right now. This shapes where we start,
              not where we end up.
            </p>
          </div>
          <div
            role="group"
            aria-label="What brings you here"
            className="flex flex-wrap gap-2.5"
          >
            {content.onboarding_reason_choices.map((reason) => {
              const isPicked = answers.reasons.includes(reason);
              return (
                <button
                  key={reason}
                  type="button"
                  aria-pressed={isPicked}
                  onClick={() => toggleReason(reason)}
                  className={`min-h-11 cursor-pointer rounded-full border px-4 py-2.5 text-sm font-medium ${
                    isPicked
                      ? "border-blue bg-blue-tint text-ink"
                      : "border-line-strong bg-transparent text-ink-body"
                  }`}
                >
                  {reason}
                </button>
              );
            })}
          </div>
          <label className={fieldLabel}>
            <span>
              In your own words{" "}
              <span className="font-normal text-ink-muted">(optional)</span>
            </span>
            <textarea
              className={inputField}
              rows={3}
              maxLength={2000}
              placeholder="e.g. I’ve been running on autopilot since starting a new job and want to feel more like myself."
              value={answers.note}
              onChange={(event) => change({ note: event.target.value })}
            />
          </label>
        </section>
      ) : null}

      {step === LOCATION_STEP ? (
        <section className="flex flex-col gap-7">
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
              countryFromBrowserUsed ? "Filled in from your browser" : undefined
            }
          />
        </section>
      ) : null}

      {step === CHECK_INS_STEP ? (
        <section className="flex flex-col gap-7">
          <div className="flex flex-col gap-3">
            <h1 className={stepHeading}>Should I check in?</h1>
            <p className="m-0 text-[17px] text-ink-soft">
              Now and then I can message you first on Telegram — a hello to see
              how you are. I choose the moment, and sometimes I’ll stay quiet to
              give you space.
            </p>
          </div>
          <div className="flex items-center justify-between gap-4 rounded-panel border border-line bg-white p-5">
            <span className="flex flex-col">
              <span className="font-semibold">Check-ins</span>
              <span className="text-caption text-ink-muted">
                Off unless you turn them on
              </span>
            </span>
            <Switch
              label="Check-ins"
              checked={answers.checkInsEnabled}
              onChange={(checkInsEnabled) => change({ checkInsEnabled })}
            />
          </div>
          {answers.checkInsEnabled ? (
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-2.5">
                <span className="text-sm font-semibold">
                  How often, at most
                </span>
                <CheckInFrequencyPicker
                  value={answers.checkInFrequency}
                  onChange={(checkInFrequency) => change({ checkInFrequency })}
                />
              </div>
              <div className="flex flex-col gap-2.5">
                <span className="text-sm font-semibold">Quiet hours</span>
                <QuietHoursFields
                  start={answers.quietHoursStart}
                  end={answers.quietHoursEnd}
                  onStartChange={(quietHoursStart) =>
                    change({ quietHoursStart })
                  }
                  onEndChange={(quietHoursEnd) => change({ quietHoursEnd })}
                />
                <p className="m-0 text-caption text-ink-muted">
                  Never in your quiet hours, in your time zone:{" "}
                  {timeZoneLabel(answers.timeZone)}.
                </p>
              </div>
            </div>
          ) : null}
          <p className="m-0 text-caption text-ink-muted">
            You can change this any time on your Check-ins page.
          </p>
        </section>
      ) : null}

      {step === MEMORY_STEP ? (
        <section className="flex flex-col gap-7">
          <div className="flex flex-col gap-3">
            <h1 className={stepHeading}>Can I remember things?</h1>
            {paragraphs(content.user_memory_explanation).map((paragraph) => (
              <p key={paragraph} className="m-0 text-[17px] text-ink-soft">
                {paragraph}
              </p>
            ))}
          </div>
          <div className="flex items-center justify-between gap-4 rounded-panel border border-line bg-white p-5">
            <span className="font-semibold">Remember meaningful details</span>
            <Switch
              label="Remember meaningful details"
              checked={answers.userMemoryEnabled}
              onChange={(userMemoryEnabled) => change({ userMemoryEnabled })}
            />
          </div>
          {saveFailed ? (
            <p
              role="alert"
              className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3 text-sm text-danger-deep"
            >
              We couldn’t save your answers. Please try again.
            </p>
          ) : null}
        </section>
      ) : null}

      {step === TELEGRAM_STEP ? (
        <section className="flex flex-col gap-6">
          <div className="flex flex-col gap-3">
            <h1 className={stepHeading}>Let’s meet on Telegram.</h1>
            <p className="m-0 text-[17px] text-ink-soft">
              That’s where we’ll talk. Linking takes one tap.
            </p>
          </div>
          <TelegramConnectionCard />
        </section>
      ) : null}

      <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-line pt-6">
        {step > HELLO_STEP ? (
          <button
            type="button"
            className={secondaryButton}
            onClick={() => setStep(step - 1)}
          >
            Back
          </button>
        ) : (
          <span />
        )}
        {step < TELEGRAM_STEP ? (
          <button
            type="button"
            className={primaryButton}
            disabled={!canContinue}
            onClick={next}
          >
            {isSaving ? "Saving…" : "Continue"}
          </button>
        ) : (
          <Link href="/" className={quietButton}>
            Skip for now
          </Link>
        )}
      </div>
    </div>
  );
}
