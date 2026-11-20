"use client";

import { useState } from "react";

import { EditorLabel } from "@/components/EditorLabel";
import { FormEditor } from "@/components/FormEditor";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { PersonaTabs } from "@/components/PersonaTabs";
import { SaveBar } from "@/components/SaveBar";
import { SavedNote } from "@/components/SavedNote";
import {
  type PersonaTab,
  personaTabDetails,
  searchWithPersonaTab,
} from "@/lib/persona";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { lastSavedNote, textSetting } from "@/lib/settings";
import {
  useAdminSettings,
  useSaveAdminSettings,
} from "@/lib/use-admin-settings";

/**
 * The admin Persona page's editor: the Voice and Outlook tabs, then the
 * chosen text's name and hint, and its editor with its save bar. Each tab
 * keeps its own unsaved text while the other is shown.
 *
 * @param props - `initialTab` is the tab shown first, from `?tab=`.
 * @returns The editor, or a loading panel or error with Try again.
 */
export function PersonaEditor({ initialTab }: { initialTab: PersonaTab }) {
  const settingsQuery = useAdminSettings();
  const saveSettings = useSaveAdminSettings();
  const [tab, setTab] = useState<PersonaTab>(initialTab);
  const [drafts, setDrafts] = useState<Record<PersonaTab, string | null>>({
    voice: null,
    outlook: null,
  });
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

  const details = personaTabDetails(tab);
  const savedText = textSetting(settings, details.settingKey);
  const text = drafts[tab] ?? savedText;
  const isDirty = text !== savedText;
  const hintId = `${details.settingKey}-hint`;

  function setDraft(draft: string | null) {
    setDrafts((current) => ({ ...current, [tab]: draft }));
  }

  function chooseTab(next: PersonaTab) {
    setTab(next);
    saveSettings.reset();
    const search = searchWithPersonaTab(window.location.search, next);
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${search}`,
    );
  }

  function saveText() {
    const savedTab = tab;
    saveSettings.mutate(
      { [details.settingKey]: text },
      {
        onSuccess: () =>
          setDrafts((current) => ({ ...current, [savedTab]: null })),
      },
    );
  }

  return (
    <>
      <PersonaTabs selected={tab} onSelect={chooseTab} />
      <EditorLabel
        label={details.name}
        hint={settings[details.settingKey]?.hint ?? ""}
        hintId={hintId}
      />
      <FormEditor
        label={details.editorLabel}
        caption={lastSavedNote(settings, [details.settingKey])}
        describedById={hintId}
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
          saveLabel={details.saveLabel}
          idleNote={details.idleNote}
          onDiscard={() => {
            setDraft(null);
            saveSettings.reset();
          }}
          onSave={saveText}
        />
      </FormEditor>
      {saveSettings.isSuccess ? (
        <SavedNote>{details.savedNote}</SavedNote>
      ) : null}
    </>
  );
}
