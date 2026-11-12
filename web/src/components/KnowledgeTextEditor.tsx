"use client";

import { useRef, useState, type ReactNode } from "react";

import {
  CodeMirrorEditor,
  type CodeMirrorEditorHandle,
} from "@/components/CodeMirrorEditor";
import { EditorToolbarButton } from "@/components/EditorToolbarButton";
import { MarkdownPreview } from "@/components/MarkdownPreview";
import { editorIcons } from "@/lib/editor-icons";
import { describeLength } from "@/lib/text-stats";

type View = "edit" | "preview" | "split";

const paneHeight = "h-[min(68vh,640px)] min-h-[320px]";

/**
 * The Knowledge text editor: the document's Markdown with line numbers,
 * highlighting and find, an Edit / Preview / Split switch (Split only on
 * wide screens) and a status bar with the word and character count.
 *
 * @param props - `value` is the text; `readOnly` hides editing controls;
 *   `label` names the editor for screen readers; `statusNote` is shown at
 *   the end of the status bar.
 * @returns The editor.
 */
export function KnowledgeTextEditor({
  value,
  readOnly = false,
  label,
  statusNote,
}: {
  value: string;
  readOnly?: boolean;
  label: string;
  statusNote?: ReactNode;
}) {
  const editorRef = useRef<CodeMirrorEditorHandle>(null);
  const [view, setView] = useState<View>("edit");

  const views: { view: View; label: string; wideOnly: boolean }[] = [
    { view: "edit", label: readOnly ? "Text" : "Edit", wideOnly: false },
    { view: "preview", label: "Preview", wideOnly: false },
    { view: "split", label: "Split", wideOnly: true },
  ];

  function openFind() {
    if (view === "preview") {
      setView("edit");
    }
    requestAnimationFrame(() => editorRef.current?.openFind());
  }

  return (
    <div className="flex flex-col rounded-card border border-line bg-white focus-within:border-blue">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-t-card border-b border-line bg-subtle px-2.5 py-2">
        <div
          role="toolbar"
          aria-label="Text tools"
          className="flex flex-wrap items-center gap-0.5"
        >
          <EditorToolbarButton
            label={readOnly ? "Find" : "Find & replace"}
            shortcut="Ctrl/⌘ F"
            keyShortcuts="Control+F Meta+F"
            iconPath={editorIcons.find}
            onClick={openFind}
          />
        </div>
        <div
          role="group"
          aria-label="View"
          className="inline-flex rounded-full border border-line-strong bg-white p-0.5"
        >
          {views.map((option) => (
            <button
              key={option.view}
              type="button"
              aria-pressed={view === option.view}
              onClick={() => setView(option.view)}
              className={`${option.wideOnly ? "hidden lg:inline-flex" : "inline-flex"} min-h-8 cursor-pointer items-center rounded-full border-0 px-3.5 text-[13px] font-medium ${
                view === option.view
                  ? "bg-ink text-white"
                  : "bg-transparent text-ink-soft hover:text-ink"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className={view === "split" ? "grid lg:grid-cols-2" : ""}>
        <div hidden={view === "preview"} className={paneHeight}>
          <CodeMirrorEditor
            ref={editorRef}
            value={value}
            readOnly={readOnly}
            label={label}
          />
        </div>
        {view !== "edit" ? (
          <section
            aria-label="Preview"
            className={`${paneHeight} overflow-y-auto px-6 py-5 ${
              view === "split"
                ? "border-t border-line lg:border-l lg:border-t-0"
                : ""
            }`}
          >
            <MarkdownPreview text={value} />
          </section>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 rounded-b-card border-t border-line bg-subtle px-4 py-2 text-caption text-ink-muted">
        <span>{describeLength(value)}</span>
        {statusNote ? <span>{statusNote}</span> : null}
      </div>
    </div>
  );
}
