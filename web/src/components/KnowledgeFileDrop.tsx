"use client";

import type { DragEvent } from "react";

/**
 * The drop area for a Knowledge file: drop a text, Markdown or PDF file on
 * it, or choose one.
 *
 * @param props - `file` is the chosen file, if any; `inputKey` changes to
 *   clear the file input; `onChoose` gets the chosen file, or null.
 * @returns The drop area.
 */
export function KnowledgeFileDrop({
  file,
  inputKey,
  onChoose,
}: {
  file: File | null;
  inputKey: number;
  onChoose: (file: File | null) => void;
}) {
  function dropFile(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    onChoose(event.dataTransfer.files[0] ?? null);
  }

  return (
    <label
      onDragOver={(event) => event.preventDefault()}
      onDrop={dropFile}
      className="flex cursor-pointer flex-col items-center gap-1.5 rounded-[14px] border-[1.5px] border-dashed border-line-strong bg-white px-4 py-7 text-center"
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className="text-blue"
      >
        <path d="M12 16V4M7 9l5-5 5 5M4 16v4h16v-4" />
      </svg>
      <span className="font-medium">Drop a file or choose one</span>
      <span className="text-caption text-ink-muted">
        {file ? file.name : "Text, Markdown or PDF · up to 20 MB"}
      </span>
      <input
        key={inputKey}
        type="file"
        accept=".txt,.md,.markdown,.pdf"
        className="sr-only"
        onChange={(event) => onChoose(event.target.files?.[0] ?? null)}
      />
    </label>
  );
}
