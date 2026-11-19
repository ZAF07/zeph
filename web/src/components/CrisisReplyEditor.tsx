"use client";

import { useState } from "react";

import { FormEditor } from "@/components/FormEditor";
import { FormSectionHeading } from "@/components/FormSectionHeading";
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

const crisisReplyKey = "crisis_reply";

/**
 * The Safety page's Crisis Reply section: the wording sent when the
 * Safeguard detects a crisis, with `{helplines}` where the Helplines go, in
 * the form template's editor and save bar.
 *
 * @returns The section, or a loading panel or error with Try again.
 */
export function CrisisReplyEditor() {
  const settingsQuery = useAdminSettings();
  const saveSettings = useSaveAdminSettings();
  const [draft, setDraft] = useState<string | null>(null);
  const settings = settingsQuery.data;

  if (!settings) {
    if (settingsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load the Crisis Reply"
          body="Zeph keeps using the last saved Crisis Reply."
          onRetry={() => void settingsQuery.refetch()}
        />
      );
    }
    return <LoadingPanel shape="card" label="Loading Crisis Reply" />;
  }

  const saved = textSetting(settings, crisisReplyKey);
  const value = draft ?? saved;
  const isDirty = value !== saved;

  function saveCrisisReply() {
    saveSettings.mutate(
      { [crisisReplyKey]: value },
      { onSuccess: () => setDraft(null) },
    );
  }

  return (
    <section
      aria-labelledby="crisis-reply-heading"
      className="flex flex-col gap-3"
    >
      <FormSectionHeading
        id="crisis-reply-heading"
        title="Crisis Reply"
        caption={
          <>
            Sent immediately when Safeguard flags risk, instead of a normal
            reply. <code className="font-mono">{"{helplines}"}</code> is
            replaced with the User’s country list.
          </>
        }
      />
      <FormEditor
        label="Crisis Reply wording"
        caption={lastSavedNote(settings, [crisisReplyKey])}
        size="short"
        value={value}
        onChange={(text) => {
          setDraft(text);
          saveSettings.reset();
        }}
      >
        <SaveBar
          placement="inside"
          isDirty={isDirty}
          isSaving={saveSettings.isPending}
          failedMessage={saveFailedMessage(
            saveSettings.error,
            "Couldn’t save. Zeph keeps using the last saved Crisis Reply.",
          )}
          canSave={isDirty && value.trim() !== ""}
          saveLabel="Save Crisis Reply"
          onDiscard={() => {
            setDraft(null);
            saveSettings.reset();
          }}
          onSave={saveCrisisReply}
        />
      </FormEditor>
      {saveSettings.isSuccess ? <SavedNote>Saved.</SavedNote> : null}
    </section>
  );
}
