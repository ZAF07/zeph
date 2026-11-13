"use client";

import { useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { Switch } from "@/components/Switch";
import { notAvailableText } from "@/lib/features";
import { paragraphs } from "@/lib/paragraphs";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Photo Viewing section: a switch that saves straight away, with the
 * Admin-worded explanation of what happens to photos, including that every
 * photo is still checked for safety.
 *
 * @param props - `enabled` is the saved setting; `available` is false when
 *   an Admin has Photo Viewing off for the User, which disables the switch;
 *   `explanation` is the Photo Viewing explanation from platform settings;
 *   `changedInChatAt` is when it was last changed in chat, if it was;
 *   `timeZone` is the User's.
 * @returns The section.
 */
export function PhotoViewingSetting({
  enabled,
  available,
  explanation,
  changedInChatAt,
  timeZone,
}: {
  enabled: boolean;
  available: boolean;
  explanation: string;
  changedInChatAt: string | undefined;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const [isEnabled, setIsEnabled] = useState(enabled);
  const [isSaving, setIsSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);
  const [changedAt, setChangedAt] = useState(changedInChatAt);

  async function savePhotoViewingSetting(next: boolean) {
    setIsSaving(true);
    setSaveFailed(false);
    try {
      const me = await apiClient.updatePreferences({
        photo_viewing_enabled: next,
      });
      setIsEnabled(me.photo_viewing_enabled);
      setChangedAt(me.changed_in_chat.photo_viewing);
    } catch {
      setSaveFailed(true);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section
      aria-labelledby="photo-viewing-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-8"
    >
      <div className="flex items-center justify-between gap-4">
        <h2
          id="photo-viewing-heading"
          className="m-0 text-[17px] font-semibold"
        >
          Look at my photos
        </h2>
        <Switch
          label="Look at my photos"
          checked={isEnabled}
          disabled={isSaving || !available}
          onChange={(next) => void savePhotoViewingSetting(next)}
        />
      </div>
      {available ? null : (
        <p className="m-0 text-sm font-medium text-ink-soft">
          {notAvailableText}
        </p>
      )}
      <ChangedInChatCaption changedAt={changedAt} timeZone={timeZone} />
      {paragraphs(explanation).map((paragraph) => (
        <p key={paragraph} className="m-0 text-[15px] text-ink-soft">
          {paragraph}
        </p>
      ))}
      {saveFailed ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t change that. Please try again.
        </p>
      ) : null}
    </section>
  );
}
