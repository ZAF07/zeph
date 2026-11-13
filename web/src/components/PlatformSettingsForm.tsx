"use client";

import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import {
  ApiError,
  type AdminSettings,
  type SettingValue,
} from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";
import { useAdminSettings } from "@/lib/use-admin-settings";

type NumberField = {
  key: string;
  label: string;
  caption: string;
  unit: string;
  note?: string;
};

type TextField = {
  key: string;
  label: string;
  caption: string;
};

type SaveState =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved" }
  | { kind: "failed"; message: string };

/** The number settings on this page, grouped by section. */
const numberSections: { heading: string; fields: NumberField[] }[] = [
  {
    heading: "Conversations",
    fields: [
      {
        key: "conversation_quiet_gap_minutes",
        label: "Conversation quiet gap",
        caption: "Minutes of silence before a Conversation ends.",
        unit: "min",
      },
      {
        key: "daily_message_limit",
        label: "Daily message limit",
        caption: "Per User. Safety replies never count toward it.",
        unit: "msgs",
      },
    ],
  },
  {
    heading: "Check-ins",
    fields: [
      {
        key: "check_in_ignore_threshold",
        label: "Ignore threshold",
        caption:
          "Unanswered Check-ins in a row before Zeph pauses and asks once about fewer.",
        unit: "in a row",
      },
    ],
  },
  {
    heading: "Photos",
    fields: [
      {
        key: "photo_retry_count",
        label: "Photo retries",
        caption:
          "Extra tries when a photo fails to download or be looked at, before Zeph says it didn’t come through.",
        unit: "tries",
      },
      {
        key: "photo_album_wait_seconds",
        label: "Album wait",
        caption:
          "Seconds to wait after an album’s last photo arrives, before Zeph answers all of it in one reply.",
        unit: "sec",
      },
      {
        key: "photo_album_max_photos",
        label: "Most photos per album",
        caption:
          "Photos Zeph looks at in one album. It mentions any it didn’t look at.",
        unit: "photos",
      },
    ],
  },
  {
    heading: "Stickers",
    fields: [
      {
        key: "personal_stickers_limit",
        label: "Most Personal Stickers per User",
        caption:
          "Stickers Zeph keeps from one User. When it would keep more, it drops the one used longest ago.",
        unit: "stickers",
      },
    ],
  },
  {
    heading: "Data",
    fields: [
      {
        key: "message_retention_days",
        label: "Message retention",
        caption:
          "Messages are deleted after this many days. Shown to Users on Account & privacy.",
        unit: "days",
        note: "Shortening applies to existing messages within a minute.",
      },
    ],
  },
];

/** The daily limit row; Web Search itself is switched on the Features page. */
const webSearchLimitField: NumberField = {
  key: "web_search_daily_limit",
  label: "Per-user daily web search limit",
  caption: "Searches and page reads per User, reset at their midnight.",
  unit: "per day",
};

/** The shared wording on this page. */
const textFields: TextField[] = [
  {
    key: "ai_notice",
    label: "AI notice",
    caption: "— shown in onboarding and on the Dashboard",
  },
  {
    key: "ai_notice_short",
    label: "Short AI notice",
    caption: "— always shown at the foot of the Dashboard sidebar",
  },
  {
    key: "user_memory_explanation",
    label: "Memory explanation",
    caption: "— shown when asking for User Memory consent",
  },
  {
    key: "photo_viewing_explanation",
    label: "Photo Viewing explanation",
    caption: "— shown with the Photo Viewing switch on Account & privacy",
  },
  {
    key: "check_in_fewer_message",
    label: "“Would you like fewer?” message",
    caption: "— sent once when a User reaches the ignore threshold",
  },
  {
    key: "daily_limit_reply",
    label: "Limit-reached reply",
    caption: "— sent in Telegram when a User hits the daily limit",
  },
  {
    key: "onboarding_unfinished_reply",
    label: "“Finish onboarding first” reply",
    caption:
      "— sent in Telegram when someone uses a connection link before finishing onboarding; keep {dashboard_url}",
  },
  {
    key: "photo_not_viewed_note",
    label: "“Didn’t come through” note",
    caption: "— tells Zeph to say honestly that a photo couldn’t be viewed",
  },
  {
    key: "photo_viewing_off_note",
    label: "“Photo Viewing off” note",
    caption:
      "— tells Zeph to say plainly it didn’t look at a photo while Photo Viewing is off",
  },
];

const numberKeys = [
  ...numberSections.flatMap((section) =>
    section.fields.map((field) => field.key),
  ),
  webSearchLimitField.key,
];

const allKeys = [...numberKeys, ...textFields.map((field) => field.key)];

const wholeNumber = /^\d+$/;

const settingRow =
  "flex flex-wrap items-center justify-between gap-x-5 gap-y-3 border-t border-line px-5 py-3.5";

/**
 * Builds the form's starting values from the saved settings.
 *
 * @param settings - The saved settings.
 * @returns Each field's value as typed text.
 */
function savedDrafts(settings: AdminSettings): Record<string, string> {
  return Object.fromEntries(
    allKeys.map((key) => [key, textSetting(settings, key)]),
  );
}

/**
 * Turns a field's typed text into the value the backend keeps.
 *
 * @param key - The setting's key.
 * @param value - The typed text.
 * @returns A number, or the text itself.
 */
function settingValue(key: string, value: string): SettingValue {
  return numberKeys.includes(key) ? Number(value) : value;
}

/**
 * The admin Platform settings page's form: timings, message retention, web
 * search and shared wording, saved together with one button.
 *
 * @returns The form, or a loading block or error with Try again.
 */
export function PlatformSettingsForm() {
  const { state, reload, save } = useAdminSettings();
  const [drafts, setDrafts] = useState<Record<string, string> | null>(null);
  const [saveState, setSaveState] = useState<SaveState>({ kind: "idle" });

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading settings"
        className="h-[360px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (state.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load platform settings"
        body="The platform keeps running on the last saved values."
        onRetry={reload}
      />
    );
  }

  const saved = savedDrafts(state.settings);
  const values = drafts ?? saved;
  const changedKeys = allKeys.filter((key) => values[key] !== saved[key]);
  const isValid =
    numberKeys.every((key) => wholeNumber.test(values[key] ?? "")) &&
    textFields.every((field) => (values[field.key] ?? "").trim() !== "");
  const canSave =
    changedKeys.length > 0 && isValid && saveState.kind !== "saving";

  function numberRow(field: NumberField) {
    return (
      <div key={field.key} className={settingRow}>
        <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-0.5">
          <label htmlFor={field.key} className="font-semibold">
            {field.label}
          </label>
          <span className="text-caption text-ink-muted">{field.caption}</span>
        </span>
        <span className="flex flex-col gap-1.5">
          <span className="flex items-center gap-2">
            <input
              id={field.key}
              className={`${inputField} w-[110px]`}
              type="number"
              inputMode="numeric"
              aria-describedby={field.note ? `${field.key}-note` : undefined}
              value={values[field.key] ?? ""}
              onChange={(event) => edit(field.key, event.target.value)}
            />
            <span className="text-caption text-ink-muted">{field.unit}</span>
          </span>
          {field.note ? (
            <span
              id={`${field.key}-note`}
              className="max-w-[220px] text-caption text-ink-muted"
            >
              {field.note}
            </span>
          ) : null}
        </span>
      </div>
    );
  }

  function edit(key: string, value: string) {
    setDrafts({ ...values, [key]: value });
    setSaveState({ kind: "idle" });
  }

  async function saveChanges() {
    setSaveState({ kind: "saving" });
    const changes: Record<string, SettingValue> = Object.fromEntries(
      changedKeys.map((key) => [key, settingValue(key, values[key] ?? "")]),
    );
    try {
      await save(changes);
      setDrafts(null);
      setSaveState({ kind: "saved" });
    } catch (error) {
      setSaveState({
        kind: "failed",
        message:
          error instanceof ApiError && error.status === 422 && error.detail
            ? error.detail
            : "Couldn’t save. The platform keeps running on the last saved values.",
      });
    }
  }

  return (
    <div className="flex flex-col gap-[30px]">
      {numberSections.map((section) => (
        <section
          key={section.heading}
          aria-label={section.heading}
          className="flex flex-col rounded-card border border-line bg-white"
        >
          <h2 className="m-0 px-5 pb-2 pt-4 text-[17px] font-semibold">
            {section.heading}
          </h2>
          {section.fields.map(numberRow)}
        </section>
      ))}

      <section
        aria-label="Web search"
        className="flex flex-col rounded-card border border-line bg-white"
      >
        <h2 className="m-0 px-5 pb-2 pt-4 text-[17px] font-semibold">
          Web search
        </h2>
        {numberRow(webSearchLimitField)}
      </section>

      <section
        aria-label="Wording"
        className="flex flex-col rounded-card border border-line bg-white"
      >
        <h2 className="m-0 px-5 pb-2 pt-4 text-[17px] font-semibold">
          Wording
        </h2>
        <div className="flex flex-col gap-4 px-5 pb-5">
          {textFields.map((field) => (
            <label key={field.key} className={fieldLabel}>
              <span>
                {field.label}{" "}
                <span className="text-caption font-normal text-ink-muted">
                  {field.caption}
                </span>
              </span>
              <textarea
                className={`${inputField} resize-y leading-relaxed`}
                rows={3}
                value={values[field.key] ?? ""}
                onChange={(event) => edit(field.key, event.target.value)}
              />
            </label>
          ))}
        </div>
      </section>

      {saveState.kind === "failed" ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {saveState.message}
        </p>
      ) : null}

      <div className="sticky bottom-4 flex flex-wrap items-center justify-between gap-3 rounded-card border border-line bg-white px-4 py-3 shadow-[0_12px_24px_-16px_rgba(0,0,0,0.35)]">
        <span className="text-caption text-ink-muted">
          {lastSavedNote(state.settings, allKeys)}
          {saveState.kind === "saved" ? (
            <span role="status" className="ml-2 text-blue-deep">
              Saved
            </span>
          ) : null}
        </span>
        <span className="flex gap-2">
          <button
            type="button"
            className={secondaryButton}
            disabled={changedKeys.length === 0}
            onClick={() => {
              setDrafts(null);
              setSaveState({ kind: "idle" });
            }}
          >
            Discard
          </button>
          <button
            type="button"
            className={primaryButton}
            disabled={!canSave}
            onClick={() => void saveChanges()}
          >
            {saveState.kind === "saving" ? "Saving…" : "Save settings"}
          </button>
        </span>
      </div>
    </div>
  );
}
