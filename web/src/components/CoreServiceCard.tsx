"use client";

import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { ExtraPromptField } from "@/components/ExtraPromptField";
import { fieldLabel, inputField } from "@/components/form-styles";
import {
  ApiError,
  type AdminSettings,
  type CoreService,
  type ExtraPrompt,
  type SettingValue,
} from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";

type SaveState =
  { kind: "idle" } | { kind: "saving" } | { kind: "failed"; message: string };

const SAVE_FAILED_MESSAGE =
  "Couldn’t save. The last saved prompt and model stay in use.";

/**
 * One core service's card: which model it uses, its prompt and any extra
 * prompts (like a tool description), saved together. Grouped extra prompts
 * sit in groups that are folded shut until clicked. The prompt is combined
 * with the Persona when the service runs. When the backend refuses a save,
 * the card shows its reason.
 *
 * @param props - `service` is the core service, `modelChoices` the models
 *   Admins can pick, `settings` the saved settings, and `onSave` saves new
 *   values and rejects if the backend refuses them.
 * @returns The card.
 */
export function CoreServiceCard({
  service,
  modelChoices,
  settings,
  onSave,
}: {
  service: CoreService;
  modelChoices: string[];
  settings: AdminSettings;
  onSave: (values: Record<string, SettingValue>) => Promise<void>;
}) {
  const savedModel = textSetting(settings, service.model_key);
  const savedPrompt = textSetting(settings, service.prompt_key);
  const [model, setModel] = useState(savedModel);
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
  const [saveState, setSaveState] = useState<SaveState>({ kind: "idle" });

  const isDirty =
    model !== savedModel ||
    prompt !== savedPrompt ||
    extraKeys.some((key) => extraPrompts[key] !== savedExtraPrompts[key]);
  const allFilled = [
    prompt,
    ...extraKeys.map((key) => extraPrompts[key]),
  ].every((text) => text?.trim());
  const canSave = isDirty && allFilled && saveState.kind !== "saving";
  const headingId = `service-${service.prompt_key}`;

  async function save() {
    setSaveState({ kind: "saving" });
    try {
      await onSave({
        [service.prompt_key]: prompt,
        [service.model_key]: model,
        ...extraPrompts,
      });
      setPrompt(prompt.trim());
      setExtraPrompts(
        Object.fromEntries(
          Object.entries(extraPrompts).map(([key, text]) => [key, text.trim()]),
        ),
      );
      setSaveState({ kind: "idle" });
    } catch (failure) {
      setSaveState({
        kind: "failed",
        message:
          failure instanceof ApiError &&
          failure.status === 422 &&
          failure.detail
            ? failure.detail
            : SAVE_FAILED_MESSAGE,
      });
    }
  }

  function extraPromptField(extraPrompt: ExtraPrompt) {
    return (
      <ExtraPromptField
        key={extraPrompt.key}
        prompt={extraPrompt}
        value={extraPrompts[extraPrompt.key] ?? ""}
        onChange={(text) => {
          setExtraPrompts({ ...extraPrompts, [extraPrompt.key]: text });
          setSaveState({ kind: "idle" });
        }}
      />
    );
  }

  return (
    <section
      aria-labelledby={headingId}
      className="flex flex-col rounded-card border border-line bg-white"
    >
      <div className="flex flex-col gap-1 px-5 pb-3 pt-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id={headingId} className="m-0 text-[17px] font-semibold">
            {service.name}
          </h2>
          <span className="inline-flex items-center rounded-full bg-code px-2.5 py-[3px] text-xs font-medium text-ink-body">
            {service.runs_when}
          </span>
        </div>
        <p className="m-0 text-sm text-ink-soft">{service.description}</p>
      </div>
      <div className="flex flex-col gap-3 px-5 pb-4">
        <label className={fieldLabel}>
          Model
          <select
            className={inputField}
            value={model}
            onChange={(event) => {
              setModel(event.target.value);
              setSaveState({ kind: "idle" });
            }}
          >
            {modelChoices.map((choice) => (
              <option key={choice} value={choice}>
                {choice}
              </option>
            ))}
          </select>
        </label>
        <label className={fieldLabel}>
          Prompt
          <textarea
            className={`${inputField} resize-y font-mono text-[13.5px] leading-relaxed`}
            rows={8}
            value={prompt}
            onChange={(event) => {
              setPrompt(event.target.value);
              setSaveState({ kind: "idle" });
            }}
          />
        </label>
        {service.extra_prompts.map(extraPromptField)}
        {service.extra_prompt_groups.map((group) => (
          <details
            key={group.name}
            className="group rounded-input border border-line"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3.5 py-3 text-sm font-semibold [&::-webkit-details-marker]:hidden">
              {group.name}
              <span
                aria-hidden="true"
                className="text-ink-muted transition-transform group-open:rotate-90"
              >
                ›
              </span>
            </summary>
            <div className="flex flex-col gap-3 border-t border-line px-3.5 pb-3.5 pt-3">
              {group.prompts.map(extraPromptField)}
            </div>
          </details>
        ))}
        {saveState.kind === "failed" ? (
          <p role="alert" className="m-0 text-sm text-danger-deep">
            {saveState.message}
          </p>
        ) : null}
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
        <span className="text-caption text-ink-muted">
          {lastSavedNote(settings, [
            service.prompt_key,
            service.model_key,
            ...extraKeys,
          ])}
        </span>
        <button
          type="button"
          className={secondaryButton}
          disabled={!canSave}
          onClick={() => void save()}
        >
          {saveState.kind === "saving" ? "Saving…" : "Save"}
        </button>
      </div>
    </section>
  );
}
