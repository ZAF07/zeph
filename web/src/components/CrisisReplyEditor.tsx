"use client";

import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { ApiError } from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";
import {
  useAdminSettings,
  useSaveAdminSettings,
} from "@/lib/use-admin-settings";

const crisisReplyKey = "crisis_reply";

/**
 * The Safety page's Crisis Reply section: the wording sent when the
 * Safeguard detects a crisis, with `{helplines}` where the Helplines go.
 *
 * @returns The editor, or a loading block or error with Try again.
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
    return (
      <div
        aria-busy="true"
        aria-label="Loading Crisis Reply"
        className="h-[280px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const saved = textSetting(settings, crisisReplyKey);
  const value = draft ?? saved;
  const canSave =
    value !== saved && value.trim() !== "" && !saveSettings.isPending;
  const { error } = saveSettings;
  const failureMessage =
    error instanceof ApiError && error.status === 422 && error.detail
      ? error.detail
      : "Couldn’t save. Zeph keeps using the last saved Crisis Reply.";

  function saveCrisisReply() {
    saveSettings.mutate(
      { [crisisReplyKey]: value },
      { onSuccess: () => setDraft(null) },
    );
  }

  return (
    <section
      aria-labelledby="crisis-reply-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-5"
    >
      <div className="flex flex-col gap-1">
        <h2 id="crisis-reply-heading" className="m-0 text-[17px] font-semibold">
          Crisis Reply
        </h2>
        <p className="m-0 text-caption text-ink-muted">
          Sent immediately when Safeguard flags risk, instead of a normal reply.{" "}
          <code className="rounded bg-code px-1 font-mono">
            {"{helplines}"}
          </code>{" "}
          is replaced with the User’s country list.
        </p>
      </div>
      <label className={fieldLabel}>
        <span>Crisis Reply wording</span>
        <textarea
          className={`${inputField} resize-y leading-relaxed`}
          rows={7}
          value={value}
          onChange={(event) => {
            setDraft(event.target.value);
            saveSettings.reset();
          }}
        />
      </label>
      {saveSettings.isError ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {failureMessage}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-caption text-ink-muted">
          {lastSavedNote(settings, [crisisReplyKey])}
          {saveSettings.isSuccess ? (
            <span role="status" className="ml-2 text-blue-deep">
              Saved
            </span>
          ) : null}
        </span>
        <button
          type="button"
          className={primaryButton}
          disabled={!canSave}
          onClick={saveCrisisReply}
        >
          {saveSettings.isPending ? "Saving…" : "Save Crisis Reply"}
        </button>
      </div>
    </section>
  );
}
