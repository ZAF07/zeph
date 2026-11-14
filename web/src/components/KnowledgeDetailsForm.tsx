"use client";

import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import {
  ApiError,
  type KnowledgeDetailsChange,
  type KnowledgeDocumentWithText,
} from "@/lib/api-client";
import { formatDay } from "@/lib/dates";
import {
  knowledgeFileTypeLabels,
  knowledgeTraditions,
} from "@/lib/knowledge-labels";

type Flash = { text: string; isError: boolean };

/**
 * A Knowledge document's Details card: its title, source / author,
 * tradition and "when it helps" as a form with Save, and its type and added
 * day. Saving takes effect straight away, without re-indexing. Shows the
 * backend's reason if it refuses.
 *
 * @param props - `knowledgeDocument` is the document; `onSave` sends the
 *   changed details and resolves with the saved document.
 * @returns The form.
 */
export function KnowledgeDetailsForm({
  knowledgeDocument,
  onSave,
}: {
  knowledgeDocument: KnowledgeDocumentWithText;
  onSave: (
    change: KnowledgeDetailsChange,
  ) => Promise<KnowledgeDocumentWithText>;
}) {
  const [title, setTitle] = useState(knowledgeDocument.title);
  const [source, setSource] = useState(knowledgeDocument.source);
  const [tradition, setTradition] = useState(knowledgeDocument.tradition);
  const [whenItHelps, setWhenItHelps] = useState(
    knowledgeDocument.when_it_helps,
  );
  const [saved, setSaved] = useState({
    title: knowledgeDocument.title,
    source: knowledgeDocument.source,
    tradition: knowledgeDocument.tradition,
    whenItHelps: knowledgeDocument.when_it_helps,
  });
  const [flash, setFlash] = useState<Flash | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const traditionChoices = knowledgeTraditions.includes(saved.tradition)
    ? knowledgeTraditions
    : [saved.tradition, ...knowledgeTraditions];
  const hasChanges =
    title !== saved.title ||
    source !== saved.source ||
    tradition !== saved.tradition ||
    whenItHelps !== saved.whenItHelps;
  const fixedDetails = [
    {
      term: "Type",
      value: `${knowledgeFileTypeLabels[knowledgeDocument.file_type]} · ${knowledgeDocument.file_name}`,
    },
    { term: "Added", value: formatDay(knowledgeDocument.created_at) },
  ];
  const canSave = hasChanges && title.trim() !== "" && source.trim() !== "";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) {
      return;
    }
    setIsSaving(true);
    setFlash(null);
    try {
      const savedDocument = await onSave({
        title,
        source,
        tradition,
        when_it_helps: whenItHelps,
      });
      setTitle(savedDocument.title);
      setSource(savedDocument.source);
      setTradition(savedDocument.tradition);
      setWhenItHelps(savedDocument.when_it_helps);
      setSaved({
        title: savedDocument.title,
        source: savedDocument.source,
        tradition: savedDocument.tradition,
        whenItHelps: savedDocument.when_it_helps,
      });
      setFlash({
        text: "Details saved. Replies use them straight away.",
        isError: false,
      });
    } catch (saveError) {
      setFlash({
        text:
          saveError instanceof ApiError && saveError.detail
            ? saveError.detail
            : "Couldn’t save the details. Please try again.",
        isError: true,
      });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form
      aria-labelledby="document-details-heading"
      onSubmit={(event) => void submit(event)}
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-6"
    >
      <h2
        id="document-details-heading"
        className="m-0 text-[17px] font-semibold"
      >
        Details
      </h2>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(220px,100%),1fr))] gap-3">
        <label className={fieldLabel}>
          Title
          <input
            className={inputField}
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label className={fieldLabel}>
          Source / author
          <input
            className={inputField}
            type="text"
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
            {traditionChoices.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="flex flex-col gap-2">
        <label className={fieldLabel}>
          When it helps
          <textarea
            className={`${inputField} min-h-24 resize-y`}
            rows={3}
            value={whenItHelps}
            aria-describedby="when-it-helps-caption"
            onChange={(event) => setWhenItHelps(event.target.value)}
          />
        </label>
        <p id="when-it-helps-caption" className={fieldCaption}>
          {saved.whenItHelps === ""
            ? "Not drafted yet. Until you write it, Zeph only has the title to go on."
            : "Zeph reads this to decide whether the document fits what someone needs."}
        </p>
      </div>
      <dl className="m-0 grid grid-cols-[repeat(auto-fit,minmax(min(220px,100%),1fr))] gap-x-3 gap-y-4">
        {fixedDetails.map((detail) => (
          <div key={detail.term} className="flex min-w-0 flex-col gap-1">
            <dt className="font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted">
              {detail.term}
            </dt>
            <dd className="m-0 break-words text-[15px]">{detail.value}</dd>
          </div>
        ))}
      </dl>
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
        className={`${primaryButton} self-start`}
        disabled={!canSave || isSaving}
      >
        {isSaving ? "Saving…" : "Save details"}
      </button>
    </form>
  );
}
