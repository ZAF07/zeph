"use client";

import { useState } from "react";

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
  caption: string;
  unit: string;
  note?: string;
};

type TextField = {
  key: string;
  label: string;
  caption: string;
};

const checkInGapsKey = "check_in_hours_between";

/** One field per Check-in Frequency; together they save the Check-in gaps. */
const checkInGapFields: (NumberField & { frequency: CheckInFrequency })[] =
  checkInFrequencyOptions.map((option) => ({
    key: `${checkInGapsKey}.${option.value}`,
    frequency: option.value,
    label: `Gap for “${option.label}”`,
    caption: "Fewest hours between two Check-ins for a User who picked it.",
    unit: "hours",
  }));

const checkInGapKeys = checkInGapFields.map((field) => field.key);

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
        key: "message_wait_seconds",
        label: "Message wait",
        caption:
          "Seconds Zeph waits after a User’s last text or photo, then answers everything they sent in one reply.",
        unit: "sec",
      },
      {
        key: "typing_repeat_seconds",
        label: "Typing repeat",
        caption:
          "Telegram hides “typing” after about 5 seconds, so while a reply is being written Zeph shows it again this often, until the reply starts.",
        unit: "sec",
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
    heading: "Memory",
    fields: [
      {
        key: "older_summaries_per_reply",
        label: "Most older Conversations per reply",
        caption:
          "When Zeph looks up the past, how many older Conversation Summaries it may add, beyond the newest ones.",
        unit: "summaries",
      },
      {
        key: "older_summaries_closeness_percent",
        label: "Older Conversation closeness bar",
        caption:
          "How close in meaning an older Summary must be to what Zeph looks up. Real matches score about 70–80; unrelated ones up to about 65.",
        unit: "%",
      },
      {
        key: "life_threads_per_reply",
        label: "Most Life Threads per reply",
        caption:
          "How many of the User’s Life Threads a message can remind Zeph of. Open ones come first.",
        unit: "threads",
      },
      {
        key: "life_threads_closeness_percent",
        label: "Life Thread closeness bar",
        caption:
          "How close in meaning a Thread’s story must be to the User’s last few messages. A Thread naming someone or something they mention always counts.",
        unit: "%",
      },
      {
        key: "life_thread_brushed_off_wait_days",
        label: "Wait after a brushed-off Life Thread",
        caption:
          "How long Zeph waits before bringing up a Thread again after the User brushed it off. One they asked to drop is never brought up again.",
        unit: "days",
      },
      {
        key: "move_outcomes_per_understanding",
        label: "Most Move Outcomes per Understanding",
        caption:
          "How many of the User’s past Move Outcomes, closest first, Zeph sees before each reply, so it picks help that has worked for them in moments like this.",
        unit: "outcomes",
      },
      {
        key: "move_outcomes_closeness_percent",
        label: "Move Outcome closeness bar",
        caption:
          "How close in meaning a Move Outcome’s situation and feeling must be to the User’s last few messages. Real matches score about 75–85; unrelated ones up to about 62.",
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
        caption:
          "How many of the things Zeph has been wondering about it may bring up in one Conversation. 0 means none.",
        unit: "per chat",
      },
      {
        key: "curiosities_waiting_limit",
        label: "Most Curiosities waiting at once",
        caption:
          "When a Conversation’s end makes more, Zeph closes the oldest waiting ones.",
        unit: "waiting",
      },
      {
        key: "curiosity_check_ins_per_week",
        label: "Most Curiosity Check-ins per week",
        caption:
          "How many “Something I’ve been wondering” Check-ins a User can get in any 7 days. 0 means none.",
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
        caption:
          "How close in meaning a passage must be to what Zeph searches for, inside the documents it chose. Fitting passages score about 65–75; unrelated ones about 50.",
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
        caption:
          "Unanswered Check-ins in a row before Zeph pauses and asks once about fewer.",
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
        caption:
          "Extra tries when a photo fails to download or be looked at, before Zeph says it didn’t come through.",
        unit: "tries",
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
      {
        key: "sticker_adding_quiet_gap_minutes",
        label: "Sticker adding quiet gap",
        caption:
          "Minutes without a sticker before adding stickers in chat ends and Zeph says what was added.",
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
    key: "memory_off_chat_line",
    label: "“Memory off” line in chat",
    caption:
      "— always sent as its own message after the reply when a User turns memory off in chat",
  },
  {
    key: "data_deleted_reply",
    label: "“Data deleted” reply",
    caption: "— sent in Telegram once a User’s data is deleted in chat",
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

/**
 * Reads one field's saved value as text; a Check-in gap field reads its
 * frequency's hours.
 *
 * @param settings - The saved settings.
 * @param key - The field's key.
 * @returns The value as text, or "" if it is missing.
 */
function savedText(settings: AdminSettings, key: string): string {
  const gapField = checkInGapFields.find((field) => field.key === key);
  if (!gapField) {
    return textSetting(settings, key);
  }
  const gaps = settings[checkInGapsKey]?.value;
  const hours = typeof gaps === "object" ? gaps[gapField.frequency] : undefined;
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
  return numberKeys.includes(key) ? Number(value) : value;
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
    textFields.every((field) => (values[field.key] ?? "").trim() !== "");
  const isDirty = changedKeys.length > 0;

  function numberRow(field: NumberField) {
    const noteId = `${field.key}-note`;
    return (
      <FieldRow
        key={field.key}
        title={field.label}
        caption={field.caption}
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

  function numberSection(
    heading: string,
    fields: NumberField[],
    loadedSettings: AdminSettings,
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
            fields.map((field) =>
              checkInGapKeys.includes(field.key) ? checkInGapsKey : field.key,
            ),
          )}
        >
          {fields.map(numberRow)}
        </FieldRows>
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
        numberSection(section.heading, section.fields, settings),
      )}
      {numberSection("Web search", [webSearchLimitField], settings)}

      <section aria-label="Wording" className="flex flex-col gap-3">
        <FormSectionHeading
          title="Wording"
          caption={lastSavedNote(
            settings,
            textFields.map((field) => field.key),
          )}
        />
        {textFields.map((field) => (
          <FormEditor
            key={field.key}
            label={field.label}
            size="short"
            caption={
              <>
                <span className="text-text">{field.label}</span> {field.caption}
              </>
            }
            value={values[field.key] ?? ""}
            onChange={(value) => edit(field.key, value)}
          />
        ))}
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
