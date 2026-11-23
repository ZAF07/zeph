"use client";

import { useState } from "react";

import { EditorLabel } from "@/components/EditorLabel";
import { FieldNumber } from "@/components/FieldNumber";
import { FieldRow } from "@/components/FieldRow";
import { FieldRows } from "@/components/FieldRows";
import { FormEditor } from "@/components/FormEditor";
import { FormSectionHeading } from "@/components/FormSectionHeading";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SaveBar } from "@/components/SaveBar";
import { SavedNote } from "@/components/SavedNote";
import type {
  AdminSettings,
  CheckInFrequency,
  SettingValue,
} from "@/lib/api-client";
import { checkInFrequencyOptions } from "@/lib/check-ins";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { lastSavedNote, textSetting } from "@/lib/settings";
import {
  useAdminSettings,
  useSaveAdminSettings,
} from "@/lib/use-admin-settings";

type NumberField = {
  key: string;
  label: string;
  unit: string;
  note?: string;
};

type TextField = {
  key: string;
  label: string;
};

const checkInGapsKey = "check_in_hours_between";

/** One field per Check-in Frequency; together they save the Check-in gaps. */
const checkInGapFields: (NumberField & { frequency: CheckInFrequency })[] =
  checkInFrequencyOptions.map((option) => ({
    key: `${checkInGapsKey}.${option.value}`,
    frequency: option.value,
    label: `Gap for “${option.label}”`,
    unit: "hours",
  }));

const checkInGapKeys = checkInGapFields.map((field) => field.key);

/** The trailing words, edited as one comma-separated text. */
const trailingWordsField: TextField = {
  key: "message_wait_trailing_words",
  label: "Trailing words",
};

/** The number settings on this page, grouped by section, with any editors below them. */
const numberSections: {
  heading: string;
  fields: NumberField[];
  editors?: TextField[];
}[] = [
  {
    heading: "Conversations",
    editors: [trailingWordsField],
    fields: [
      {
        key: "conversation_quiet_gap_minutes",
        label: "Conversation quiet gap",
        unit: "min",
      },
      {
        key: "message_wait_finished_seconds",
        label: "Wait after a finished text",
        unit: "sec",
      },
      {
        key: "message_wait_trailing_seconds",
        label: "Wait after a trailing text",
        unit: "sec",
      },
      {
        key: "message_wait_seconds",
        label: "Wait after any other text",
        unit: "sec",
      },
      {
        key: "message_wait_long_text_words",
        label: "Long text",
        unit: "words",
      },
      {
        key: "typing_repeat_seconds",
        label: "Typing repeat",
        unit: "sec",
      },
      {
        key: "daily_message_limit",
        label: "Daily message limit",
        unit: "msgs",
      },
      {
        key: "recent_messages_hours",
        label: "Recent messages",
        unit: "hours",
      },
      {
        key: "recent_messages_cap",
        label: "Recent messages cap",
        unit: "msgs",
      },
    ],
  },
  {
    heading: "Memory",
    fields: [
      {
        key: "older_summaries_per_reply",
        label: "Most older Conversations per reply",
        unit: "summaries",
      },
      {
        key: "older_summaries_closeness_percent",
        label: "Older Conversation closeness bar",
        unit: "%",
      },
      {
        key: "life_threads_per_reply",
        label: "Most Life Threads in mind",
        unit: "threads",
      },
      {
        key: "life_threads_texts_to_search",
        label: "Texts searched for Life Threads",
        unit: "texts",
      },
      {
        key: "life_threads_closeness_percent",
        label: "Life Thread closeness bar",
        unit: "%",
      },
      {
        key: "life_thread_brushed_off_wait_days",
        label: "Wait after a brushed-off Life Thread",
        unit: "days",
      },
      {
        key: "pattern_closeness_percent",
        label: "Pattern closeness bar",
        unit: "%",
      },
      {
        key: "pattern_pushed_back_wait_days",
        label: "Wait after a pushed-back Pattern",
        unit: "days",
      },
      {
        key: "move_outcomes_per_understanding",
        label: "Most Move Outcomes per Understanding",
        unit: "outcomes",
      },
      {
        key: "move_outcomes_closeness_percent",
        label: "Move Outcome closeness bar",
        unit: "%",
      },
    ],
  },
  {
    heading: "Curiosities",
    fields: [
      {
        key: "curiosities_per_conversation",
        label: "Most Curiosities raised per Conversation",
        unit: "per chat",
      },
      {
        key: "curiosities_waiting_limit",
        label: "Most Curiosities waiting at once",
        unit: "waiting",
      },
      {
        key: "curiosity_check_ins_per_week",
        label: "Most Curiosity Check-ins per week",
        unit: "per week",
      },
    ],
  },
  {
    heading: "Knowledge",
    fields: [
      {
        key: "knowledge_closeness_percent",
        label: "Knowledge closeness bar",
        unit: "%",
      },
    ],
  },
  {
    heading: "Check-ins",
    fields: [
      {
        key: "check_in_ignore_threshold",
        label: "Ignore threshold",
        unit: "in a row",
      },
      ...checkInGapFields,
    ],
  },
  {
    heading: "Photos",
    fields: [
      {
        key: "photo_retry_count",
        label: "Photo retries",
        unit: "tries",
      },
      {
        key: "photo_album_max_photos",
        label: "Most photos per album",
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
        unit: "stickers",
      },
      {
        key: "sticker_adding_quiet_gap_minutes",
        label: "Sticker adding quiet gap",
        unit: "min",
      },
    ],
  },
  {
    heading: "Data",
    fields: [
      {
        key: "message_retention_days",
        label: "Message retention",
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
  unit: "per day",
};

/** The shared wording on this page. */
const textFields: TextField[] = [
  {
    key: "memory_off_chat_line",
    label: "“Memory off” line in chat",
  },
  {
    key: "data_deleted_reply",
    label: "“Data deleted” reply",
  },
  {
    key: "check_in_fewer_message",
    label: "“Would you like fewer?” message",
  },
  {
    key: "daily_limit_reply",
    label: "Limit-reached reply",
  },
  {
    key: "onboarding_unfinished_reply",
    label: "“Finish onboarding first” reply",
  },
  {
    key: "photo_not_viewed_note",
    label: "“Didn’t come through” note",
  },
  {
    key: "photo_viewing_off_note",
    label: "“Photo Viewing off” note",
  },
];

const numberKeys = [
  ...numberSections.flatMap((section) =>
    section.fields.map((field) => field.key),
  ),
  webSearchLimitField.key,
];

const allKeys = [
  ...numberKeys,
  ...textFields.map((field) => field.key),
  trailingWordsField.key,
];

const wholeNumber = /^\d+$/;

/**
 * Names the saved setting a field belongs to: each Check-in gap field
 * belongs to the one Check-in gaps setting.
 *
 * @param key - The field's key.
 * @returns The setting's key.
 */
function settingKeyFor(key: string): string {
  return checkInGapKeys.includes(key) ? checkInGapsKey : key;
}

/**
 * Reads one field's saved value as text; a Check-in gap field reads its
 * frequency's hours.
 *
 * @param settings - The saved settings.
 * @param key - The field's key.
 * @returns The value as text, or "" if it is missing.
 */
function savedText(settings: AdminSettings, key: string): string {
  const value = settings[key]?.value;
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  const gapField = checkInGapFields.find((field) => field.key === key);
  if (!gapField) {
    return textSetting(settings, key);
  }
  const gaps = settings[checkInGapsKey]?.value;
  const hours =
    typeof gaps === "object" && !Array.isArray(gaps)
      ? gaps[gapField.frequency]
      : undefined;
  return hours === undefined ? "" : String(hours);
}

/**
 * Builds the form's starting values from the saved settings.
 *
 * @param settings - The saved settings.
 * @returns Each field's value as typed text.
 */
function savedDrafts(settings: AdminSettings): Record<string, string> {
  return Object.fromEntries(
    allKeys.map((key) => [key, savedText(settings, key)]),
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
  if (key === trailingWordsField.key) {
    return wordList(value);
  }
  return numberKeys.includes(key) ? Number(value) : value;
}

/**
 * Splits comma-separated words into a list, leaving out blank ones.
 *
 * @param value - The typed text, e.g. "and, ok so".
 * @returns The words, trimmed.
 */
function wordList(value: string): string[] {
  return value
    .split(",")
    .map((word) => word.trim())
    .filter((word) => word !== "");
}

/**
 * The admin Platform settings page's form: timings, Check-in gaps, message
 * retention, web search and shared wording, in the form template's field
 * rows and editors, saved together with one save bar.
 *
 * @returns The form, or a loading block or error with Try again.
 */
export function PlatformSettingsForm() {
  const settingsQuery = useAdminSettings();
  const saveSettings = useSaveAdminSettings();
  const [drafts, setDrafts] = useState<Record<string, string> | null>(null);
  const settings = settingsQuery.data;

  if (!settings) {
    if (settingsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load platform settings"
          body="The platform keeps running on the last saved values."
          onRetry={() => void settingsQuery.refetch()}
        />
      );
    }
    return <LoadingPanel shape="card" label="Loading settings" />;
  }

  const saved = savedDrafts(settings);
  const values = drafts ?? saved;
  const changedKeys = allKeys.filter((key) => values[key] !== saved[key]);
  const isValid =
    numberKeys.every((key) => wholeNumber.test(values[key] ?? "")) &&
    textFields.every((field) => (values[field.key] ?? "").trim() !== "") &&
    wordList(values[trailingWordsField.key] ?? "").length > 0;
  const isDirty = changedKeys.length > 0;

  function hintFor(key: string, loadedSettings: AdminSettings): string {
    return loadedSettings[settingKeyFor(key)]?.hint ?? "";
  }

  function numberRow(field: NumberField, loadedSettings: AdminSettings) {
    const noteId = `${field.key}-note`;
    return (
      <FieldRow
        key={field.key}
        title={field.label}
        caption={hintFor(field.key, loadedSettings)}
        htmlFor={field.key}
        note={
          field.note ? (
            <div id={noteId} className="text-[12px] text-soft">
              {field.note}
            </div>
          ) : null
        }
      >
        <FieldNumber
          id={field.key}
          value={values[field.key] ?? ""}
          unit={field.unit}
          describedById={field.note ? noteId : undefined}
          onChange={(value) => edit(field.key, value)}
        />
      </FieldRow>
    );
  }

  function textEditor(field: TextField, loadedSettings: AdminSettings) {
    const hintId = `${field.key}-hint`;
    return (
      <div key={field.key} className="flex flex-col gap-3">
        <EditorLabel
          label={field.label}
          hint={hintFor(field.key, loadedSettings)}
          hintId={hintId}
        />
        <FormEditor
          label={field.label}
          size="short"
          describedById={hintId}
          caption={lastSavedNote(loadedSettings, [field.key])}
          value={values[field.key] ?? ""}
          onChange={(value) => edit(field.key, value)}
        />
      </div>
    );
  }

  function numberSection(
    heading: string,
    fields: NumberField[],
    loadedSettings: AdminSettings,
    editors: TextField[] = [],
  ) {
    return (
      <section
        key={heading}
        aria-label={heading}
        className="flex flex-col gap-3"
      >
        <FormSectionHeading title={heading} />
        <FieldRows
          footnote={lastSavedNote(
            loadedSettings,
            fields.map((field) => settingKeyFor(field.key)),
          )}
        >
          {fields.map((field) => numberRow(field, loadedSettings))}
        </FieldRows>
        {editors.map((field) => textEditor(field, loadedSettings))}
      </section>
    );
  }

  function edit(key: string, value: string) {
    setDrafts({ ...values, [key]: value });
    saveSettings.reset();
  }

  function saveChanges() {
    const changes: Record<string, SettingValue> = Object.fromEntries(
      changedKeys
        .filter((key) => !checkInGapKeys.includes(key))
        .map((key) => [key, settingValue(key, values[key] ?? "")]),
    );
    if (changedKeys.some((key) => checkInGapKeys.includes(key))) {
      changes[checkInGapsKey] = Object.fromEntries(
        checkInGapFields.map((field) => [
          field.frequency,
          Number(values[field.key] ?? ""),
        ]),
      );
    }
    saveSettings.mutate(changes, { onSuccess: () => setDrafts(null) });
  }

  return (
    <>
      {numberSections.map((section) =>
        numberSection(
          section.heading,
          section.fields,
          settings,
          section.editors,
        ),
      )}
      {numberSection("Web search", [webSearchLimitField], settings)}

      <section aria-label="Wording" className="flex flex-col gap-3">
        <FormSectionHeading title="Wording" />
        {textFields.map((field) => textEditor(field, settings))}
      </section>

      <SaveBar
        placement="alone"
        sticky
        isDirty={isDirty}
        isSaving={saveSettings.isPending}
        failedMessage={saveFailedMessage(
          saveSettings.error,
          "Couldn’t save. The platform keeps running on the last saved values.",
        )}
        canSave={isDirty && isValid}
        saveLabel="Save settings"
        onDiscard={() => {
          setDrafts(null);
          saveSettings.reset();
        }}
        onSave={saveChanges}
      />
      {saveSettings.isSuccess ? <SavedNote>Saved.</SavedNote> : null}
    </>
  );
}
