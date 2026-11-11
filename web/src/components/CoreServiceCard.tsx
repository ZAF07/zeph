"use client";

import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import type {
  AdminSettings,
  CoreService,
  SettingValue,
} from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";

type SaveState = "idle" | "saving" | "failed";

/**
 * One core service's card: which model it uses and its prompt, saved
 * together. The prompt is combined with the Persona when the service runs.
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
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const isDirty = model !== savedModel || prompt !== savedPrompt;
  const canSave = isDirty && prompt.trim() !== "" && saveState !== "saving";
  const headingId = `service-${service.prompt_key}`;

  async function save() {
    setSaveState("saving");
    try {
      await onSave({
        [service.prompt_key]: prompt,
        [service.model_key]: model,
      });
      setPrompt(prompt.trim());
      setSaveState("idle");
    } catch {
      setSaveState("failed");
    }
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
              setSaveState("idle");
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
              setSaveState("idle");
            }}
          />
        </label>
        {saveState === "failed" ? (
          <p role="alert" className="m-0 text-sm text-danger-deep">
            Couldn’t save. The last saved prompt and model stay in use.
          </p>
        ) : null}
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
        <span className="text-caption text-ink-muted">
          {lastSavedNote(settings, [service.prompt_key, service.model_key])}
        </span>
        <button
          type="button"
          className={secondaryButton}
          disabled={!canSave}
          onClick={() => void save()}
        >
          {saveState === "saving" ? "Saving…" : "Save"}
        </button>
      </div>
    </section>
  );
}
