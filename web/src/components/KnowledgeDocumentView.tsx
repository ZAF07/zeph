"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import {
  compactSecondaryButton,
  dangerButton,
} from "@/components/button-styles";
import { KnowledgeDetailsForm } from "@/components/KnowledgeDetailsForm";
import { KnowledgeStatusPill } from "@/components/KnowledgeStatusPill";
import { KnowledgeTextEditor } from "@/components/KnowledgeTextEditor";
import { LoadFailed } from "@/components/LoadFailed";
import {
  ApiError,
  type KnowledgeDetailsChange,
  type KnowledgeDocumentWithText,
} from "@/lib/api-client";
import { knowledgeStatusLabels } from "@/lib/knowledge-labels";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "not-found" }
  | { kind: "failed" }
  | { kind: "loaded"; document: KnowledgeDocumentWithText };

type Flash = { text: string; isError: boolean };

const pendingCheckMilliseconds = 3000;

const libraryPath = "/admin/knowledge";

/**
 * Says what an Admin sees in place of a document's text before it has any.
 *
 * @param knowledgeDocument - The document, which has no text yet.
 * @returns A short explanation.
 */
function noTextExplanation(
  knowledgeDocument: KnowledgeDocumentWithText,
): string {
  if (knowledgeDocument.status === "pending") {
    return "The file is being read. Its text will show here when it’s ready.";
  }
  return "No text could be read from this file, so Zeph doesn’t draw on it.";
}

/**
 * One Knowledge document's page: its details (editable), status and why it
 * failed, the text Zeph draws on in the read-only text editor, Retry when it
 * failed and Delete. Checks again every few seconds while the document is
 * pending.
 *
 * @param props - `documentId` is the document to show.
 * @returns The page body, or a loading, not-found or error state.
 */
export function KnowledgeDocumentView({ documentId }: { documentId: string }) {
  const apiClient = useApiClient();
  const router = useRouter();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [flash, setFlash] = useState<Flash | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setState({
        kind: "loaded",
        document: await apiClient.getKnowledgeDocument(documentId),
      });
    } catch (error) {
      setState({
        kind:
          error instanceof ApiError && error.status === 404
            ? "not-found"
            : "failed",
      });
    }
  }, [apiClient, documentId]);

  useEffect(() => {
    void load();
  }, [load]);

  const isPending =
    state.kind === "loaded" && state.document.status === "pending";

  useEffect(() => {
    if (!isPending) {
      return;
    }
    const timer = setTimeout(() => void load(), pendingCheckMilliseconds);
    return () => clearTimeout(timer);
  }, [isPending, load, state]);

  async function saveDetails(
    knowledgeDocument: KnowledgeDocumentWithText,
    change: KnowledgeDetailsChange,
  ) {
    const saved = await apiClient.updateKnowledgeDocumentDetails(
      knowledgeDocument.id,
      change,
    );
    setState({ kind: "loaded", document: saved });
    return saved;
  }

  async function retry(knowledgeDocument: KnowledgeDocumentWithText) {
    setIsBusy(true);
    setFlash(null);
    try {
      await apiClient.retryKnowledgeDocument(knowledgeDocument.id);
      await load();
    } catch {
      setFlash({
        text: `Couldn’t retry ${knowledgeDocument.title}. Please try again.`,
        isError: true,
      });
    } finally {
      setIsBusy(false);
    }
  }

  async function remove(knowledgeDocument: KnowledgeDocumentWithText) {
    if (
      !window.confirm(
        `Delete ${knowledgeDocument.title}? Zeph will stop drawing on it.`,
      )
    ) {
      return;
    }
    setIsBusy(true);
    setFlash(null);
    try {
      await apiClient.deleteKnowledgeDocument(knowledgeDocument.id);
      router.push(libraryPath);
    } catch {
      setFlash({
        text: `Couldn’t delete ${knowledgeDocument.title}. Please try again.`,
        isError: true,
      });
      setIsBusy(false);
    }
  }

  const backLink = (
    <Link href={libraryPath} className="w-fit text-sm font-medium">
      ← Knowledge
    </Link>
  );

  if (state.kind === "loading") {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <div
          aria-busy="true"
          aria-label="Loading the document"
          className="h-[420px] rounded-xl border border-line bg-subtle"
        />
      </div>
    );
  }

  if (state.kind === "not-found") {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <h1 className="m-0 text-[22px] font-medium tracking-[-0.02em]">
            This document no longer exists
          </h1>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            It may have been deleted by another Admin.
          </p>
          <Link href={libraryPath} className="mt-2 text-sm font-medium">
            Back to Knowledge
          </Link>
        </div>
      </div>
    );
  }

  if (state.kind === "failed") {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <LoadFailed
          title="Couldn’t load the document"
          body="Zeph keeps using documents that are already Ready."
          onRetry={() => void load()}
        />
      </div>
    );
  }

  const knowledgeDocument = state.document;
  const statusLabel = knowledgeStatusLabels[knowledgeDocument.status].label;

  return (
    <div className="flex flex-col gap-9">
      <div className="flex flex-col gap-5">
        {backLink}
        <AdminPageHeader
          title={knowledgeDocument.title}
          lead="The text Zeph draws on from this document. Only “Ready” documents are used in replies."
        />
        <div className="flex flex-wrap items-center gap-2">
          <KnowledgeStatusPill status={knowledgeDocument.status} />
          {knowledgeDocument.text_edited ? (
            <span className="inline-flex w-fit items-center rounded-full border border-line-strong px-2.5 py-[3px] text-xs font-medium text-ink-soft">
              Edited
            </span>
          ) : null}
        </div>
      </div>

      {flash ? (
        <p
          role="status"
          className={`m-0 rounded-xl px-4 py-3.5 text-sm ${
            flash.isError
              ? "border border-danger-line bg-danger-tint text-danger-deep"
              : "bg-blue-tint text-blue-deep"
          }`}
        >
          {flash.text}
        </p>
      ) : null}

      {knowledgeDocument.status === "failed" ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5">
          <p className="m-0 text-sm text-danger-deep">
            <span className="font-semibold">Failed: </span>
            {knowledgeDocument.failure_reason ?? "Something went wrong."}
          </p>
          <button
            type="button"
            className={`${compactSecondaryButton} bg-white`}
            disabled={isBusy}
            onClick={() => void retry(knowledgeDocument)}
          >
            Retry
          </button>
        </div>
      ) : null}

      <KnowledgeDetailsForm
        key={knowledgeDocument.id}
        knowledgeDocument={knowledgeDocument}
        onSave={(change) => saveDetails(knowledgeDocument, change)}
      />

      <section
        aria-labelledby="document-text-heading"
        className="flex flex-col gap-3"
      >
        <div className="flex flex-col gap-1">
          <h2 id="document-text-heading" className="m-0 text-h3 font-semibold">
            Text
          </h2>
          <p className="m-0 text-caption text-ink-muted">
            What Zeph draws on, as read from the file.
          </p>
        </div>
        {knowledgeDocument.text === null ? (
          <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-12 text-center">
            <span className="text-[17px] font-medium">No text yet</span>
            <p className="m-0 max-w-[34em] text-caption text-ink-muted">
              {noTextExplanation(knowledgeDocument)}
            </p>
          </div>
        ) : (
          <KnowledgeTextEditor
            value={knowledgeDocument.text}
            readOnly
            label={`Text of ${knowledgeDocument.title}`}
            statusNote={statusLabel}
          />
        )}
      </section>

      <div className="flex flex-col items-start gap-2 border-t border-line pt-6">
        <button
          type="button"
          className={dangerButton}
          disabled={isBusy}
          onClick={() => void remove(knowledgeDocument)}
        >
          Delete document
        </button>
        <p className="m-0 text-caption text-ink-muted">
          Zeph stops drawing on it straight away. This can’t be undone.
        </p>
      </div>
    </div>
  );
}
