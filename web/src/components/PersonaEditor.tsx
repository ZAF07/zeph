"use client";

import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { lastSavedNote, textSetting } from "@/lib/settings";
import {
  useAdminSettings,
  useSaveAdminSettings,
} from "@/lib/use-admin-settings";

/**
 * The admin Persona page's editor: the honesty-rules reminder, the Persona
 * text, and Discard and Save.
 *
 * @returns The editor, or a loading block or error with Try again.
 */
export function PersonaEditor() {
  const settingsQuery = useAdminSettings();
  const saveSettings = useSaveAdminSettings();
  const [draft, setDraft] = useState<string | null>(null);
  const settings = settingsQuery.data;

  const honestyNote = (
    <div
      role="note"
      className="flex flex-col gap-2 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
    >
      <strong className="font-semibold">The honesty rules must stay.</strong>
      <span>
        Whatever else you change, keep these in the Persona: Zeph says it’s an
        AI whenever it matters and never claims to be human; it isn’t a
        therapist or crisis service; it doesn’t flatter or encourage dependency;
        it supports the User’s own thinking.
      </span>
    </div>
  );

  if (!settings) {
    return (
      <>
        {honestyNote}
        {settingsQuery.isError ? (
          <LoadFailed
            title="Couldn’t load the Persona"
            body="Zeph keeps using the last saved version."
            onRetry={() => void settingsQuery.refetch()}
          />
        ) : (
          <div
            aria-busy="true"
            aria-label="Loading persona"
            className="h-[560px] rounded-card border border-line bg-subtle"
          />
        )}
      </>
    );
  }

  const savedPersona = textSetting(settings, "persona");
  const text = draft ?? savedPersona;
  const isDirty = text !== savedPersona;
  const canSave = isDirty && text.trim() !== "" && !saveSettings.isPending;

  function savePersona() {
    saveSettings.mutate({ persona: text }, { onSuccess: () => setDraft(null) });
  }

  return (
    <>
      {honestyNote}
      <section className="flex flex-col rounded-card border border-line bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <span className="text-caption text-ink-muted">
            {lastSavedNote(settings, ["persona"])}
          </span>
          <span className="font-mono text-caption text-ink-muted">
            {text.length} characters
          </span>
        </div>
        <label className="block">
          <span className="sr-only">Persona text</span>
          <textarea
            rows={26}
            value={text}
            onChange={(event) => {
              setDraft(event.target.value);
              saveSettings.reset();
            }}
            className="block min-h-[560px] w-full resize-y border-0 p-5 font-mono text-[13.5px] leading-relaxed text-ink"
          />
        </label>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3.5">
          {isDirty ? (
            <span className="inline-flex items-center rounded-full bg-yellow-tint px-2.5 py-[3px] text-xs font-medium text-yellow-deep">
              Unsaved changes
            </span>
          ) : (
            <span className="text-caption text-ink-muted">
              Changes apply to the next message after saving.
            </span>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={secondaryButton}
              disabled={!isDirty}
              onClick={() => {
                setDraft(null);
                saveSettings.reset();
              }}
            >
              Discard
            </button>
            <button
              type="button"
              className={primaryButton}
              disabled={!canSave}
              onClick={savePersona}
            >
              {saveSettings.isPending ? "Saving…" : "Save Persona"}
            </button>
          </div>
        </div>
      </section>
      {saveSettings.isSuccess ? (
        <p
          role="status"
          className="m-0 rounded-xl bg-blue-tint px-4 py-3.5 text-sm text-blue-deep"
        >
          Saved. Zeph uses it from the next message.
        </p>
      ) : null}
      {saveSettings.isError ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          Couldn’t save the Persona. Zeph keeps using the last saved version.
        </p>
      ) : null}
    </>
  );
}
