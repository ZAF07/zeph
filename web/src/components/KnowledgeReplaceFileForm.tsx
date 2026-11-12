"use client";

import { useState, type FormEvent } from "react";

import { secondaryButton } from "@/components/button-styles";
import { KnowledgeFileDrop } from "@/components/KnowledgeFileDrop";
import { ApiError, type KnowledgeDocumentWithText } from "@/lib/api-client";

type Flash = { text: string; isError: boolean };

/**
 * The "Replace file" card: a new text, Markdown or PDF file for a Knowledge
 * document, with the same drop area and rules as upload. The document keeps
 * its details and added date, and its new file is read and re-indexed.
 * Asks first when the document's text was edited, as the edits are
 * replaced. Shows the backend's reason if it refuses the file.
 *
 * @param props - `knowledgeDocument` is the document; `onReplace` sends the
 *   file and resolves with the pending document.
 * @returns The form.
 */
export function KnowledgeReplaceFileForm({
  knowledgeDocument,
  onReplace,
}: {
  knowledgeDocument: KnowledgeDocumentWithText;
  onReplace: (file: File) => Promise<KnowledgeDocumentWithText>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [flash, setFlash] = useState<Flash | null>(null);
  const [isReplacing, setIsReplacing] = useState(false);

  function chooseFile(chosen: File | null) {
    setFile(chosen);
    setFlash(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }
    if (
      knowledgeDocument.text_edited &&
      !window.confirm(
        "This document’s text was edited. Replacing the file replaces those edits with the new file’s text. Continue?",
      )
    ) {
      return;
    }
    setIsReplacing(true);
    setFlash(null);
    try {
      const replaced = await onReplace(file);
      setFile(null);
      setFileInputKey((key) => key + 1);
      setFlash({
        text: `Replaced with ${replaced.file_name}. It’s being read and indexed now.`,
        isError: false,
      });
    } catch (replaceError) {
      setFlash({
        text:
          replaceError instanceof ApiError && replaceError.detail
            ? replaceError.detail
            : "Couldn’t replace the file. Please try again.",
        isError: true,
      });
    } finally {
      setIsReplacing(false);
    }
  }

  return (
    <form
      aria-labelledby="replace-file-heading"
      onSubmit={(event) => void submit(event)}
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-6"
    >
      <div className="flex flex-col gap-1">
        <h2 id="replace-file-heading" className="m-0 text-[17px] font-semibold">
          Replace file
        </h2>
        <p className="m-0 text-caption text-ink-muted">
          Swap in a better translation or a corrected version. The title,
          source, tradition and added date stay; the new file is read and
          re-indexed.
        </p>
      </div>
      <KnowledgeFileDrop
        file={file}
        inputKey={fileInputKey}
        onChoose={chooseFile}
      />
      {flash ? (
        <p
          role={flash.isError ? "alert" : "status"}
          className={`m-0 rounded-xl px-4 py-3.5 text-sm ${
            flash.isError
              ? "border border-danger-line bg-danger-tint text-danger-deep"
              : "bg-blue-tint text-blue-deep"
          }`}
        >
          {flash.text}
        </p>
      ) : null}
      <button
        type="submit"
        className={`${secondaryButton} self-start`}
        disabled={file === null || isReplacing}
      >
        {isReplacing ? "Replacing…" : "Replace file"}
      </button>
    </form>
  );
}
