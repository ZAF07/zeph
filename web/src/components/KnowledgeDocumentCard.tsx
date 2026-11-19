"use client";

import Link from "next/link";
import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";
import { CardSaveBar } from "@/components/CardSaveBar";
import { CardTag } from "@/components/CardTag";
import { FieldRow } from "@/components/FieldRow";
import { FoldingCard } from "@/components/FoldingCard";
import type { KnowledgeDocument } from "@/lib/api-client";
import {
  knowledgeFileTypeLabels,
  knowledgeStatusLabels,
} from "@/lib/knowledge-labels";

/**
 * One Knowledge document as a card of the card list. The folded row shows
 * its title, source and tradition, its status and the day it was added.
 * Open, it shows its type, file and why it failed, read only, and a bar
 * with Open document, Retry (when it failed) and Delete. Editing happens on
 * the document's own page.
 *
 * @param props - `knowledgeDocument` is the document; `addedDay` is when it
 *   was added, written for the row; `isOpen` and `onToggle` open and fold
 *   it; `onRetry` indexes a failed one again; `onDelete` deletes it;
 *   `isChanging` turns those off while one saves.
 * @returns The card.
 */
export function KnowledgeDocumentCard({
  knowledgeDocument,
  addedDay,
  isOpen,
  onToggle,
  onRetry,
  onDelete,
  isChanging,
}: {
  knowledgeDocument: KnowledgeDocument;
  addedDay: string;
  isOpen: boolean;
  onToggle: () => void;
  onRetry: () => void;
  onDelete: () => void;
  isChanging: boolean;
}) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const isFailed = knowledgeDocument.status === "failed";
  const valueClass = "text-[15px] text-text break-all";

  return (
    <FoldingCard
      title={knowledgeDocument.title}
      summary={`${knowledgeDocument.source} · ${knowledgeDocument.tradition}`}
      tags={
        <CardTag tone={knowledgeStatusLabels[knowledgeDocument.status].tone}>
          {knowledgeStatusLabels[knowledgeDocument.status].label}
        </CardTag>
      }
      meta={addedDay}
      isDirty={false}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <ul className="m-0 list-none p-0">
        <FieldRow title="Type">
          <span className={valueClass}>
            {knowledgeFileTypeLabels[knowledgeDocument.file_type]}
          </span>
        </FieldRow>
        <FieldRow title="File">
          <span className={valueClass}>{knowledgeDocument.file_name}</span>
        </FieldRow>
        {knowledgeDocument.failure_reason ? (
          <FieldRow title="Why it failed">
            <span className="text-[15px] text-danger">
              {knowledgeDocument.failure_reason}
            </span>
          </FieldRow>
        ) : null}
      </ul>
      {isConfirmingDelete ? (
        <CardRemoveConfirm
          label="Delete this document?"
          title={`Delete “${knowledgeDocument.title}”?`}
          body="Zeph will stop drawing on it."
          confirmLabel="Delete"
          isBusy={isChanging}
          onKeep={() => setIsConfirmingDelete(false)}
          onConfirm={() => {
            setIsConfirmingDelete(false);
            onDelete();
          }}
        />
      ) : (
        <CardSaveBar
          note="Only Ready documents are used."
          isBusy={isChanging}
          removeLabel="Delete"
          onRemove={() => setIsConfirmingDelete(true)}
          actions={
            <>
              <Link
                href={`/admin/knowledge/${knowledgeDocument.id}`}
                className={secondaryButton}
              >
                Open document
              </Link>
              {isFailed ? (
                <button
                  type="button"
                  className={secondaryButton}
                  disabled={isChanging}
                  onClick={onRetry}
                >
                  Retry
                </button>
              ) : null}
            </>
          }
        />
      )}
    </FoldingCard>
  );
}
