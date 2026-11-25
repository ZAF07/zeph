"use client";

import { useState } from "react";

import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { ChevronDownIcon } from "@/components/ChevronDownIcon";
import { EditorLabel } from "@/components/EditorLabel";
import { ExtraPromptField } from "@/components/ExtraPromptField";
import { FieldRow } from "@/components/FieldRow";
import { FieldNumber } from "@/components/FieldNumber";
import { FieldRows } from "@/components/FieldRows";
import { FieldSelect } from "@/components/FieldSelect";
import { FoldingCard } from "@/components/FoldingCard";
import { FormEditor } from "@/components/FormEditor";
import { FormSectionHeading } from "@/components/FormSectionHeading";
import { SavedNote } from "@/components/SavedNote";
import { Switch } from "@/components/Switch";
import type { AdminSettings, CoreService, ExtraPrompt } from "@/lib/api-client";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { lastSavedNote, onOffSetting, textSetting } from "@/lib/settings";
import { useSaveAdminSettings } from "@/lib/use-admin-settings";

/**
 * One core service as a folding card of the card list. The folded row shows
 * its name, description and when it runs. Open, it has two groups: "Model &
 * settings", the field rows for which model it uses, whether that model
 * thinks first and any limits on what it is given, a hint under each; and
 * "Prompts", editors for its prompt and any extra prompts (like a tool
 * description) each with its name and hint above it. Grouped extra prompts
 * sit in groups that are folded shut until clicked. One save bar saves them
 * together. The prompt is combined with the Persona when the service runs.
 * When the backend refuses a save, the save bar shows its reason. While the
 * chosen model can't think, the thinking switch is off and can't be changed,
 * and thinking is saved as off.
 *
 * @param props - `service` is the core service, `modelChoices` the models
 *   Admins can pick, `modelsThatCannotThink` the ones of those that can't
 *   think, `settings` the saved settings, and `isOpen` and `onToggle` open
 *   and fold the card.
 * @returns The card.
 */
export function CoreServiceCard({
  service,
  modelChoices,
  modelsThatCannotThink,
  settings,
  isOpen,
  onToggle,
}: {
  service: CoreService;
  modelChoices: string[];
  modelsThatCannotThink: string[];
  settings: AdminSettings;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const saveSettings = useSaveAdminSettings();
  const savedModel = textSetting(settings, service.model_key);
  const savedThinking = onOffSetting(settings, service.thinking_key);
  const savedPrompt = textSetting(settings, service.prompt_key);
  const [model, setModel] = useState(savedModel);
  const [thinkingSwitch, setThinkingSwitch] = useState(savedThinking);
  const modelCanThink = !modelsThatCannotThink.includes(model);
  const thinking = modelCanThink && thinkingSwitch;
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
  const limitKeys = service.limits.map(({ key }) => key);
  const savedLimits = Object.fromEntries(
    limitKeys.map((key) => [key, textSetting(settings, key)]),
  );
  const [limits, setLimits] = useState<Record<string, string>>(savedLimits);

  const isDirty =
    model !== savedModel ||
    thinking !== savedThinking ||
    prompt !== savedPrompt ||
    extraKeys.some((key) => extraPrompts[key] !== savedExtraPrompts[key]) ||
    limitKeys.some((key) => limits[key] !== savedLimits[key]);
  const allFilled = [
    prompt,
    ...extraKeys.map((key) => extraPrompts[key]),
    ...limitKeys.map((key) => limits[key]),
  ].every((text) => text?.trim());
  const idPrefix = `service-${service.prompt_key}`;
  const modelId = `${idPrefix}-model`;
  const promptHintId = `${idPrefix}-prompt-hint`;
  const settingsGroupId = `${idPrefix}-settings`;
  const promptsGroupId = `${idPrefix}-prompts`;

  function discard() {
    setModel(savedModel);
    setThinkingSwitch(savedThinking);
    setPrompt(savedPrompt);
    setExtraPrompts(savedExtraPrompts);
    setLimits(savedLimits);
    saveSettings.reset();
  }

  function save() {
    saveSettings.mutate(
      {
        [service.prompt_key]: prompt,
        [service.model_key]: model,
        [service.thinking_key]: thinking,
        ...extraPrompts,
        ...Object.fromEntries(
          limitKeys.map((key) => [key, Number(limits[key])]),
        ),
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
        savedNote={lastSavedNote(settings, [extraPrompt.key])}
        value={extraPrompts[extraPrompt.key] ?? ""}
        onChange={(text) => {
          setExtraPrompts({ ...extraPrompts, [extraPrompt.key]: text });
          saveSettings.reset();
        }}
      />
    );
  }

  return (
    <FoldingCard
      title={service.name}
      summary={service.description}
      tags={<CardTag>{service.runs_when}</CardTag>}
      isDirty={isDirty}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <div
        role="group"
        aria-labelledby={settingsGroupId}
        className="flex flex-col gap-3"
      >
        <FormSectionHeading id={settingsGroupId} title="Model & settings" />
        <FieldRows>
          <FieldRow
            title="Model"
            caption={settings[service.model_key]?.hint}
            htmlFor={modelId}
          >
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
          <FieldRow
            title="Thinking"
            caption={settings[service.thinking_key]?.hint}
          >
            <Switch
              label={`Thinking for ${service.name}`}
              checked={thinking}
              disabled={!modelCanThink}
              onChange={(isOn) => {
                setThinkingSwitch(isOn);
                saveSettings.reset();
              }}
            />
          </FieldRow>
          {service.limits.map((limit) => {
            const limitId = `${idPrefix}-${limit.key}`;
            return (
              <FieldRow
                key={limit.key}
                title={limit.label}
                caption={limit.hint}
                htmlFor={limitId}
              >
                <FieldNumber
                  id={limitId}
                  value={limits[limit.key] ?? ""}
                  onChange={(value) => {
                    setLimits({ ...limits, [limit.key]: value });
                    saveSettings.reset();
                  }}
                />
              </FieldRow>
            );
          })}
        </FieldRows>
      </div>
      <div
        role="group"
        aria-labelledby={promptsGroupId}
        className="flex flex-col gap-3"
      >
        <FormSectionHeading id={promptsGroupId} title="Prompts" />
        <EditorLabel
          label="Prompt"
          hint={settings[service.prompt_key]?.hint ?? ""}
          hintId={promptHintId}
        />
        <FormEditor
          label="Prompt"
          describedById={promptHintId}
          caption={lastSavedNote(settings, [
            service.prompt_key,
            service.model_key,
            service.thinking_key,
            ...extraKeys,
            ...limitKeys,
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
      </div>
      <CardSaveBar
        note="Changes apply to the next message after saving."
        failedMessage={saveFailedMessage(
          saveSettings.error,
          "Couldn’t save. The last saved prompt, model and thinking stay in use.",
        )}
        isDirty={isDirty}
        canSave={isDirty && allFilled}
        isBusy={saveSettings.isPending}
        onDiscard={discard}
        onSave={save}
      />
      {saveSettings.isSuccess ? <SavedNote>Saved.</SavedNote> : null}
    </FoldingCard>
  );
}
