"use client";

import { useId, useState } from "react";

import { CardTextField } from "@/components/CardTextField";
import { FieldRow } from "@/components/FieldRow";
import { FieldSelect } from "@/components/FieldSelect";
import { KnowledgeFileDrop } from "@/components/KnowledgeFileDrop";
import { NewCardBox } from "@/components/NewCardBox";
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
 * The "Add a document" box above the Knowledge list: a file drop area,
 * title, source / author and tradition, then Cancel and Upload. Shows the
 * backend's reason if it refuses the file.
 *
 * @param props - `onUpload` sends the document and rejects if it fails;
 *   `onCancel` closes the box.
 * @returns The box.
 */
export function KnowledgeUploadBox({
  onUpload,
  onCancel,
}: {
  onUpload: (upload: KnowledgeUpload) => Promise<void>;
  onCancel: () => void;
}) {
  const fieldId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [tradition, setTradition] = useState(knowledgeTraditions[0]);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  function chooseFile(chosen: File | null) {
    setFile(chosen);
    setError(null);
    if (chosen && !title.trim()) {
      setTitle(titleFromFileName(chosen.name));
    }
  }

  async function upload() {
    if (!file) {
      return;
    }
    setIsUploading(true);
    setError(null);
    try {
      await onUpload({ file, title, source, tradition });
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
    <NewCardBox
      title="Add a document"
      failedMessage={error}
      canAdd={file !== null && title.trim() !== "" && source.trim() !== ""}
      isBusy={isUploading}
      addLabel="Upload"
      busyLabel="Uploading…"
      onCancel={onCancel}
      onAdd={() => void upload()}
    >
      <KnowledgeFileDrop file={file} inputKey={0} onChoose={chooseFile} />
      <CardTextField
        label="Title"
        placeholder="e.g. Letters to Lucilius"
        value={title}
        onChange={setTitle}
      />
      <CardTextField
        label="Source / author"
        placeholder="e.g. Seneca, trans. Gummere"
        value={source}
        onChange={setSource}
      />
      <ul className="m-0 list-none p-0">
        <FieldRow title="Tradition" htmlFor={`${fieldId}-tradition`}>
          <FieldSelect
            id={`${fieldId}-tradition`}
            value={tradition}
            options={knowledgeTraditions.map((option) => ({
              value: option,
              label: option,
            }))}
            onChange={setTradition}
          />
        </FieldRow>
      </ul>
    </NewCardBox>
  );
}
