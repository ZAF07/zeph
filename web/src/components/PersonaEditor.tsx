"use client";

import { useState } from "react";

import { EditorLabel } from "@/components/EditorLabel";
import { FormEditor } from "@/components/FormEditor";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SaveBar } from "@/components/SaveBar";
import { SavedNote } from "@/components/SavedNote";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { lastSavedNote, textSetting } from "@/lib/settings";
import {
  useAdminSettings,
  useSaveAdminSettings,
} from "@/lib/use-admin-settings";

/**
 * The admin Persona page's editor: the Persona's name and hint, then its
 * text with its save bar.
 *
 * @returns The editor, or a loading panel or error with Try again.
 */
export function PersonaEditor() {
  const settingsQuery = useAdminSettings();
  const saveSettings = useSaveAdminSettings();
  const [draft, setDraft] = useState<string | null>(null);
  const settings = settingsQuery.data;

  if (!settings) {
    if (settingsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load the Persona"
          body="Zeph keeps using the last saved version."
          onRetry={() => void settingsQuery.refetch()}
        />
      );
    }
    return <LoadingPanel shape="card" label="Loading persona" />;
  }

  const savedPersona = textSetting(settings, "persona");
  const text = draft ?? savedPersona;
  const isDirty = text !== savedPersona;

  function savePersona() {
    saveSettings.mutate({ persona: text }, { onSuccess: () => setDraft(null) });
  }

  return (
    <>
      <EditorLabel
        label="Persona"
        hint={settings.persona?.hint ?? ""}
        hintId="persona-hint"
      />
      <FormEditor
        label="Persona text"
        caption={lastSavedNote(settings, ["persona"])}
        describedById="persona-hint"
        value={text}
        onChange={(value) => {
          setDraft(value);
          saveSettings.reset();
        }}
      >
        <SaveBar
          placement="inside"
          isDirty={isDirty}
          isSaving={saveSettings.isPending}
          failedMessage={saveFailedMessage(saveSettings.error)}
          canSave={isDirty && text.trim() !== ""}
          saveLabel="Save Persona"
          onDiscard={() => {
            setDraft(null);
            saveSettings.reset();
          }}
          onSave={savePersona}
        />
      </FormEditor>
      {saveSettings.isSuccess ? (
        <SavedNote>Saved. Zeph uses it from the next message.</SavedNote>
      ) : null}
    </>
  );
}
