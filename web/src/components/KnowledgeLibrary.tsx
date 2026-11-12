"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  compactSecondaryButton,
  deleteIconButton,
} from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import { KnowledgeStatusPill } from "@/components/KnowledgeStatusPill";
import { KnowledgeUploadForm } from "@/components/KnowledgeUploadForm";
import { LoadFailed } from "@/components/LoadFailed";
import type { KnowledgeDocument, KnowledgeUpload } from "@/lib/api-client";
import { formatAddedDay } from "@/lib/dates";
import {
  knowledgeFileTypeLabels,
  knowledgeStatusOrder,
} from "@/lib/knowledge-labels";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; documents: KnowledgeDocument[] };

type Flash = { text: string; isError: boolean };

const pendingCheckMilliseconds = 3000;

const headings = [
  "Title",
  "Source / author",
  "Tradition",
  "Type",
  "Status",
  "Added",
];

const headingCell =
  "whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted";

/**
 * Writes the table caption, like "6 documents · 4 ready · 1 failed".
 *
 * @param documents - Every document in the library.
 * @returns The count of documents and of each status there is.
 */
function countsCaption(documents: KnowledgeDocument[]): string {
  const total = `${documents.length} ${
    documents.length === 1 ? "document" : "documents"
  }`;
  const perStatus = knowledgeStatusOrder
    .map((status) => ({
      status,
      count: documents.filter(
        (knowledgeDocument) => knowledgeDocument.status === status,
      ).length,
    }))
    .filter(({ count }) => count > 0)
    .map(({ status, count }) => `${count} ${status}`);
  return [total, ...perStatus].join(" · ");
}

/**
 * The admin Knowledge library: upload a document, then see each one's
 * status while it is indexed, open its page from its title, retry one that
 * failed, or delete one. Checks again every few seconds while any document
 * is pending.
 *
 * @returns The upload form and document table, or a loading, empty or error
 *   state.
 */
export function KnowledgeLibrary() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [flash, setFlash] = useState<Flash | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setState({
        kind: "loaded",
        documents: await apiClient.listKnowledgeDocuments(),
      });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  const hasPending =
    state.kind === "loaded" &&
    state.documents.some(
      (knowledgeDocument) => knowledgeDocument.status === "pending",
    );

  useEffect(() => {
    if (!hasPending) {
      return;
    }
    const timer = setTimeout(() => void load(), pendingCheckMilliseconds);
    return () => clearTimeout(timer);
  }, [hasPending, load, state]);

  async function upload(newDocument: KnowledgeUpload) {
    setFlash(null);
    const uploaded = await apiClient.uploadKnowledgeDocument(newDocument);
    setFlash({
      text: `Uploaded ${uploaded.title}. It’s being indexed now.`,
      isError: false,
    });
    await load();
  }

  async function runRowAction(
    knowledgeDocument: KnowledgeDocument,
    action: () => Promise<unknown>,
    successText: string | null,
  ) {
    setBusyId(knowledgeDocument.id);
    setFlash(null);
    try {
      await action();
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
      await load();
    } catch {
      setFlash({
        text: `Couldn’t change ${knowledgeDocument.title}. Please try again.`,
        isError: true,
      });
    } finally {
      setBusyId(null);
    }
  }

  function remove(knowledgeDocument: KnowledgeDocument) {
    if (
      !window.confirm(
        `Delete ${knowledgeDocument.title}? Zeph will stop drawing on it.`,
      )
    ) {
      return;
    }
    void runRowAction(
      knowledgeDocument,
      () => apiClient.deleteKnowledgeDocument(knowledgeDocument.id),
      `Deleted ${knowledgeDocument.title}.`,
    );
  }

  const now = new Date();

  return (
    <div className="flex flex-col gap-[30px]">
      <KnowledgeUploadForm onUpload={upload} />

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

      {state.kind === "loading" ? (
        <div
          aria-busy="true"
          aria-label="Loading documents"
          className="h-[240px] rounded-xl border border-line bg-subtle"
        />
      ) : null}

      {state.kind === "failed" ? (
        <LoadFailed
          title="Couldn’t load the document list"
          body="Zeph keeps using documents that are already Ready."
          onRetry={() => void load()}
        />
      ) : null}

      {state.kind === "loaded" && state.documents.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            The library is empty
          </span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Until you add documents, Zeph relies on general knowledge only.
            Start with a few primary texts per tradition.
          </p>
        </div>
      ) : null}

      {state.kind === "loaded" && state.documents.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-line bg-white">
          <table className="w-full min-w-[860px] border-collapse text-sm">
            <caption className="border-b border-line px-4 py-2.5 text-left text-caption text-ink-muted">
              {countsCaption(state.documents)}
            </caption>
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className={`${headingCell} text-left`}
                  >
                    {heading}
                  </th>
                ))}
                <th scope="col" className={`${headingCell} text-right`}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {state.documents.map((knowledgeDocument) => {
                const isBusy = busyId === knowledgeDocument.id;
                return (
                  <tr
                    key={knowledgeDocument.id}
                    className="border-b border-line last:border-b-0"
                  >
                    <td className="px-[18px] py-3.5 font-medium">
                      <Link
                        href={`/admin/knowledge/${knowledgeDocument.id}`}
                        className="text-ink underline decoration-line-strong underline-offset-4 hover:decoration-ink"
                      >
                        {knowledgeDocument.title}
                      </Link>
                    </td>
                    <td className="px-[18px] py-3.5">
                      {knowledgeDocument.source}
                    </td>
                    <td className="px-[18px] py-3.5">
                      {knowledgeDocument.tradition}
                    </td>
                    <td className="px-[18px] py-3.5">
                      {knowledgeFileTypeLabels[knowledgeDocument.file_type]}
                    </td>
                    <td className="px-[18px] py-3.5">
                      <span className="inline-flex flex-col gap-0.5">
                        <KnowledgeStatusPill
                          status={knowledgeDocument.status}
                        />
                        {knowledgeDocument.failure_reason ? (
                          <span className="text-caption text-ink-muted">
                            {knowledgeDocument.failure_reason}
                          </span>
                        ) : null}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-[18px] py-3.5">
                      {formatAddedDay(knowledgeDocument.created_at, now)}
                    </td>
                    <td className="whitespace-nowrap px-[18px] py-2 text-right">
                      {knowledgeDocument.status === "failed" ? (
                        <button
                          type="button"
                          className={compactSecondaryButton}
                          disabled={isBusy}
                          onClick={() =>
                            void runRowAction(
                              knowledgeDocument,
                              () =>
                                apiClient.retryKnowledgeDocument(
                                  knowledgeDocument.id,
                                ),
                              null,
                            )
                          }
                        >
                          Retry
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className={deleteIconButton}
                        aria-label={`Delete ${knowledgeDocument.title}`}
                        disabled={isBusy}
                        onClick={() => remove(knowledgeDocument)}
                      >
                        <DeleteIcon />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
