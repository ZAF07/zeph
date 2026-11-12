"use client";

import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { KnowledgeFileDrop } from "@/components/KnowledgeFileDrop";
import { ApiError, type KnowledgeUpload } from "@/lib/api-client";
import { knowledgeTraditions } from "@/lib/knowledge-labels";

/**
 * Turns a file name like "tao-te-ching.txt" into a starting title.
 *
 * @param fileName - The chosen file's name.
 * @returns The name without its extension, with dashes and underscores as
 *   spaces.
 */
function titleFromFileName(fileName: string): string {
  return fileName
    .replace(/\.[^.]+$/, "")
    .replace(/[-_]+/g, " ")
    .trim();
}

/**
 * The "Add a document" card: a file drop area, title, source / author and
 * tradition, and Upload. Shows the backend's reason if it refuses the file.
 *
 * @param props - `onUpload` sends the document; when it resolves the form
 *   is cleared.
 * @returns The form.
 */
export function KnowledgeUploadForm({
  onUpload,
}: {
  onUpload: (upload: KnowledgeUpload) => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [tradition, setTradition] = useState(knowledgeTraditions[0]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const canUpload =
    file !== null && title.trim() !== "" && source.trim() !== "";

  function chooseFile(chosen: File | null) {
    setFile(chosen);
    setError(null);
    if (chosen && !title.trim()) {
      setTitle(titleFromFileName(chosen.name));
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !canUpload) {
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      await onUpload({ file, title, source, tradition });
      setFile(null);
      setFileInputKey((key) => key + 1);
      setTitle("");
      setSource("");
      setTradition(knowledgeTraditions[0]);
    } catch (uploadError) {
      setError(
        uploadError instanceof ApiError && uploadError.detail
          ? uploadError.detail
          : "Couldn’t upload the document. Please try again.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form
      aria-labelledby="add-document-heading"
      onSubmit={(event) => void submit(event)}
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-6"
    >
      <h2 id="add-document-heading" className="m-0 text-[17px] font-semibold">
        Add a document
      </h2>
      <KnowledgeFileDrop
        file={file}
        inputKey={fileInputKey}
        onChoose={chooseFile}
      />
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(220px,100%),1fr))] gap-3">
        <label className={fieldLabel}>
          Title
          <input
            className={inputField}
            type="text"
            placeholder="e.g. Letters to Lucilius"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label className={fieldLabel}>
          Source / author
          <input
            className={inputField}
            type="text"
            placeholder="e.g. Seneca, trans. Gummere"
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
        </label>
        <label className={fieldLabel}>
          Tradition
          <select
            className={inputField}
            value={tradition}
            onChange={(event) => setTradition(event.target.value)}
          >
            {knowledgeTraditions.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>
      {error ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        className={`${primaryButton} self-start`}
        disabled={!canUpload || isUploading}
      >
        {isUploading ? "Uploading…" : "Upload"}
      </button>
    </form>
  );
}
