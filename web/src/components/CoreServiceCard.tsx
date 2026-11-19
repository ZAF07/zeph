"use client";

import { useState } from "react";

import { ChevronDownIcon } from "@/components/ChevronDownIcon";
import { ExtraPromptField } from "@/components/ExtraPromptField";
import { FieldRow } from "@/components/FieldRow";
import { FieldRows } from "@/components/FieldRows";
import { FieldSelect } from "@/components/FieldSelect";
import { FormEditor } from "@/components/FormEditor";
import { FormSectionHeading } from "@/components/FormSectionHeading";
import { SaveBar } from "@/components/SaveBar";
import { SavedNote } from "@/components/SavedNote";
import { Switch } from "@/components/Switch";
import type { AdminSettings, CoreService, ExtraPrompt } from "@/lib/api-client";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { lastSavedNote, onOffSetting, textSetting } from "@/lib/settings";
import { useSaveAdminSettings } from "@/lib/use-admin-settings";

/**
 * One core service's part of the page, from the form template: its heading,
 * field rows for which model it uses and whether that model thinks first,
 * editors for its prompt and any extra prompts (like a tool description),
 * and one save bar that saves them together. Grouped extra prompts
 * sit in groups that are folded shut until clicked. The prompt is combined
 * with the Persona when the service runs. When the backend refuses a save,
 * the save bar shows its reason.
 *
 * @param props - `service` is the core service, `modelChoices` the models
 *   Admins can pick, and `settings` the saved settings.
 * @returns The service's part of the page.
 */
export function CoreServiceCard({
  service,
  modelChoices,
  settings,
}: {
  service: CoreService;
  modelChoices: string[];
  settings: AdminSettings;
}) {
  const saveSettings = useSaveAdminSettings();
  const savedModel = textSetting(settings, service.model_key);
  const savedThinking = onOffSetting(settings, service.thinking_key);
  const savedPrompt = textSetting(settings, service.prompt_key);
  const [model, setModel] = useState(savedModel);
  const [thinking, setThinking] = useState(savedThinking);
  const [prompt, setPrompt] = useState(savedPrompt);
  const allExtraPrompts = [
    ...service.extra_prompts,
    ...service.extra_prompt_groups.flatMap((group) => group.prompts),
  ];
  const extraKeys = allExtraPrompts.map(({ key }) => key);
  const savedExtraPrompts = Object.fromEntries(
    extraKeys.map((key) => [key, textSetting(settings, key)]),
  );
  const [extraPrompts, setExtraPrompts] =
    useState<Record<string, string>>(savedExtraPrompts);

  const isDirty =
    model !== savedModel ||
    thinking !== savedThinking ||
    prompt !== savedPrompt ||
    extraKeys.some((key) => extraPrompts[key] !== savedExtraPrompts[key]);
  const allFilled = [
    prompt,
    ...extraKeys.map((key) => extraPrompts[key]),
  ].every((text) => text?.trim());
  const headingId = `service-${service.prompt_key}`;
  const modelId = `${headingId}-model`;

  function discard() {
    setModel(savedModel);
    setThinking(savedThinking);
    setPrompt(savedPrompt);
    setExtraPrompts(savedExtraPrompts);
    saveSettings.reset();
  }

  function save() {
    saveSettings.mutate(
      {
        [service.prompt_key]: prompt,
        [service.model_key]: model,
        [service.thinking_key]: thinking,
        ...extraPrompts,
      },
      {
        onSuccess: () => {
          setPrompt(prompt.trim());
          setExtraPrompts(
            Object.fromEntries(
              Object.entries(extraPrompts).map(([key, text]) => [
                key,
                text.trim(),
              ]),
            ),
          );
        },
      },
    );
  }

  function extraPromptField(extraPrompt: ExtraPrompt) {
    return (
      <ExtraPromptField
        key={extraPrompt.key}
        prompt={extraPrompt}
        value={extraPrompts[extraPrompt.key] ?? ""}
        onChange={(text) => {
          setExtraPrompts({ ...extraPrompts, [extraPrompt.key]: text });
          saveSettings.reset();
        }}
      />
    );
  }

  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <FormSectionHeading
          id={headingId}
          title={service.name}
          caption={service.description}
        />
        <span className="max-w-full rounded-pill border border-line-strong px-2.5 py-0.5 text-[12px] font-normal text-soft">
          {service.runs_when}
        </span>
      </div>
      <FieldRows>
        <FieldRow title="Model" htmlFor={modelId}>
          <FieldSelect
            id={modelId}
            value={model}
            options={modelChoices.map((choice) => ({
              value: choice,
              label: choice,
            }))}
            onChange={(choice) => {
              setModel(choice);
              saveSettings.reset();
            }}
          />
        </FieldRow>
        <FieldRow title="Thinking">
          <Switch
            label="Thinking"
            checked={thinking}
            onChange={(isOn) => {
              setThinking(isOn);
              saveSettings.reset();
            }}
          />
        </FieldRow>
      </FieldRows>
      <FormEditor
        label="Prompt"
        caption={lastSavedNote(settings, [
          service.prompt_key,
          service.model_key,
          service.thinking_key,
          ...extraKeys,
        ])}
        value={prompt}
        onChange={(text) => {
          setPrompt(text);
          saveSettings.reset();
        }}
      />
      {service.extra_prompts.map(extraPromptField)}
      {service.extra_prompt_groups.map((group) => (
        <details
          key={group.name}
          className="group rounded-card border border-line bg-panel"
        >
          <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-6 py-3 text-[15px] text-text [&::-webkit-details-marker]:hidden">
            {group.name}
            <ChevronDownIcon className="-rotate-90 text-soft transition-transform duration-150 ease-in-out group-open:rotate-0 motion-reduce:transition-none" />
          </summary>
          <div className="flex flex-col gap-3 px-6 pb-4">
            {group.prompts.map(extraPromptField)}
          </div>
        </details>
      ))}
      <SaveBar
        placement="alone"
        isDirty={isDirty}
        isSaving={saveSettings.isPending}
        failedMessage={saveFailedMessage(
          saveSettings.error,
          "Couldn’t save. The last saved prompt, model and thinking stay in use.",
        )}
        canSave={isDirty && allFilled}
        saveLabel="Save"
        onDiscard={discard}
        onSave={save}
      />
      {saveSettings.isSuccess ? <SavedNote>Saved.</SavedNote> : null}
    </section>
  );
}
