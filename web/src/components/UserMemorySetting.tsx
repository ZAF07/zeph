"use client";

import { useState } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { Switch } from "@/components/Switch";
import { paragraphs } from "@/lib/paragraphs";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The User Memory section: a switch that saves straight away, with the
 * Admin-worded explanation of what is remembered.
 *
 * @param props - `enabled` is the saved setting; `explanation` is the
 *   User Memory explanation from platform settings; `changedInChatAt` is
 *   when it was last changed in chat, if it was; `timeZone` is the User's.
 * @returns The section.
 */
export function UserMemorySetting({
  enabled,
  explanation,
  changedInChatAt,
  timeZone,
}: {
  enabled: boolean;
  explanation: string;
  changedInChatAt: string | undefined;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const [isEnabled, setIsEnabled] = useState(enabled);
  const [isSaving, setIsSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);
  const [changedAt, setChangedAt] = useState(changedInChatAt);

  async function saveUserMemorySetting(next: boolean) {
    setIsSaving(true);
    setSaveFailed(false);
    try {
      const me = await apiClient.updatePreferences({
        user_memory_enabled: next,
      });
      setIsEnabled(me.user_memory_enabled);
      setChangedAt(me.changed_in_chat.user_memory);
    } catch {
      setSaveFailed(true);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section
      aria-labelledby="memory-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-8"
    >
      <div className="flex items-center justify-between gap-4">
        <h2 id="memory-heading" className="m-0 text-[17px] font-semibold">
          Remember meaningful details
        </h2>
        <Switch
          label="Remember meaningful details"
          checked={isEnabled}
          disabled={isSaving}
          onChange={(next) => void saveUserMemorySetting(next)}
        />
      </div>
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
