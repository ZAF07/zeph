"use client";

import { useCallback, useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { EmptyState } from "@/components/EmptyState";
import { KnowledgeTextEditor } from "@/components/KnowledgeTextEditor";
import { SavedNote } from "@/components/SavedNote";
import { TextChangesReview } from "@/components/TextChangesReview";
import { ApiError, type KnowledgeDocumentWithText } from "@/lib/api-client";
import { knowledgeStatusLabels } from "@/lib/knowledge-labels";
import { useUnsavedChangesWarning } from "@/lib/use-unsaved-changes-warning";

const leaveMessage = "You have unsaved text changes. Leave and lose them?";

/**
 * A Knowledge document's Text section: the text Zeph draws on in the
 * Knowledge text editor, with an "Unsaved changes" / "Saved" state, Save
 * text (or Ctrl/⌘+S) opening "Review changes" before "Save and re-index",
 * Discard changes after confirming, and a warning before leaving with
 * unsaved changes. A document with no text yet can be given its text here,
 * once its file has been read.
 *
 * @param props - `knowledgeDocument` is the document; `onSave` saves the
 *   text and resolves with the pending document.
 * @returns The section.
 */
export function KnowledgeTextSection({
  knowledgeDocument,
  onSave,
}: {
  knowledgeDocument: KnowledgeDocumentWithText;
  onSave: (text: string) => Promise<KnowledgeDocumentWithText>;
}) {
  const [draft, setDraft] = useState<string | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const savedText = knowledgeDocument.text ?? "";
  const text = draft ?? savedText;
  const hasUnsavedChanges = draft !== null && draft !== savedText;
  useUnsavedChangesWarning(hasUnsavedChanges, leaveMessage);

  const openReview = useCallback(() => {
    if (hasUnsavedChanges) {
      setSaveError(null);
      setIsReviewing(true);
    }
  }, [hasUnsavedChanges]);

  const closeReview = useCallback(() => setIsReviewing(false), []);

  async function save() {
    setIsSaving(true);
    setSaveError(null);
    try {
      await onSave(text);
      setDraft(null);
      setIsReviewing(false);
      setSavedMessage(
        "Text saved. Zeph uses it once the document is Ready again.",
      );
    } catch (error) {
      setSaveError(
        error instanceof ApiError && error.detail
          ? error.detail
          : "Couldn’t save the text. Please try again.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  function discard() {
    if (window.confirm("Discard your unsaved text changes?")) {
      setDraft(null);
      setSavedMessage(null);
    }
  }

  function edit(value: string) {
    setDraft(value);
    setSavedMessage(null);
  }

  const isWaitingForFile =
    knowledgeDocument.text === null && knowledgeDocument.status === "pending";
  const statusLabel = knowledgeStatusLabels[knowledgeDocument.status].label;

  return (
    <section
      aria-labelledby="document-text-heading"
      className="flex flex-col gap-3"
    >
      <div className="flex flex-col gap-1">
        <h2
          id="document-text-heading"
          className="m-0 text-[17px] font-normal text-cream"
        >
          Text
        </h2>
        <p className="m-0 text-[13px] text-soft">
          {knowledgeDocument.text === null && !isWaitingForFile
            ? "No text could be read from this file. Type or paste its text, then save to make it Ready."
            : "What Zeph draws on. Saving your changes re-indexes the document."}
        </p>
      </div>

      {isWaitingForFile ? (
        <EmptyState
          title="No text yet"
          body="The file is being read. Its text will show here when it’s ready."
        />
      ) : (
        <>
          <KnowledgeTextEditor
            value={text}
            onChange={edit}
            label={`Text of ${knowledgeDocument.title}`}
            onSave={openReview}
            statusNote={
              <>
                <span className={hasUnsavedChanges ? "text-orange" : ""}>
                  {hasUnsavedChanges ? "Unsaved changes" : "Saved"}
                </span>
                {` · ${statusLabel}`}
              </>
            }
          />
          {savedMessage ? <SavedNote>{savedMessage}</SavedNote> : null}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className={primaryButton}
              disabled={!hasUnsavedChanges}
              onClick={openReview}
            >
              Save text…
            </button>
            <button
              type="button"
              className={secondaryButton}
              disabled={!hasUnsavedChanges}
              onClick={discard}
            >
              Discard changes
            </button>
          </div>
        </>
      )}

      {isReviewing ? (
        <TextChangesReview
          saved={savedText}
          edited={text}
          isSaving={isSaving}
          error={saveError}
          onConfirm={() => void save()}
          onCancel={closeReview}
        />
      ) : null}
    </section>
  );
}
