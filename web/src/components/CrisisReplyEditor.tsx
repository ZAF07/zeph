"use client";

import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { ApiError } from "@/lib/api-client";
import { lastSavedNote, textSetting } from "@/lib/settings";
import { useAdminSettings } from "@/lib/use-admin-settings";

const crisisReplyKey = "crisis_reply";

type SaveState =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved" }
  | { kind: "failed"; message: string };

/**
 * The Safety page's Crisis Reply section: the wording sent when the
 * Safeguard detects a crisis, with `{helplines}` where the Helplines go.
 *
 * @returns The editor, or a loading block or error with Try again.
 */
export function CrisisReplyEditor() {
  const { state, reload, save } = useAdminSettings();
  const [draft, setDraft] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<SaveState>({ kind: "idle" });

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading Crisis Reply"
        className="h-[280px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (state.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load the Crisis Reply"
        body="Zeph keeps using the last saved Crisis Reply."
        onRetry={reload}
      />
    );
  }

  const saved = textSetting(state.settings, crisisReplyKey);
  const value = draft ?? saved;
  const canSave =
    value !== saved && value.trim() !== "" && saveState.kind !== "saving";

  async function saveCrisisReply() {
    setSaveState({ kind: "saving" });
    try {
      await save({ [crisisReplyKey]: value });
      setDraft(null);
      setSaveState({ kind: "saved" });
    } catch (error) {
      setSaveState({
        kind: "failed",
        message:
          error instanceof ApiError && error.status === 422 && error.detail
            ? error.detail
            : "Couldn’t save. Zeph keeps using the last saved Crisis Reply.",
      });
    }
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
            setSaveState({ kind: "idle" });
          }}
        />
      </label>
      {saveState.kind === "failed" ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {saveState.message}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-caption text-ink-muted">
          {lastSavedNote(state.settings, [crisisReplyKey])}
          {saveState.kind === "saved" ? (
            <span role="status" className="ml-2 text-blue-deep">
              Saved
            </span>
          ) : null}
        </span>
        <button
          type="button"
          className={primaryButton}
          disabled={!canSave}
          onClick={() => void saveCrisisReply()}
        >
          {saveState.kind === "saving" ? "Saving…" : "Save Crisis Reply"}
        </button>
      </div>
    </section>
  );
}
