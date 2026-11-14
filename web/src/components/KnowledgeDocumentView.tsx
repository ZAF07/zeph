"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AdminPageHeader } from "@/components/AdminPageHeader";
import {
  compactSecondaryButton,
  dangerButton,
} from "@/components/button-styles";
import { KnowledgeDetailsForm } from "@/components/KnowledgeDetailsForm";
import { KnowledgeReplaceFileForm } from "@/components/KnowledgeReplaceFileForm";
import { KnowledgeStatusPill } from "@/components/KnowledgeStatusPill";
import { KnowledgeTextSection } from "@/components/KnowledgeTextSection";
import { LoadFailed } from "@/components/LoadFailed";
import {
  ApiError,
  type KnowledgeDetailsChange,
  type KnowledgeDocumentWithText,
} from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const pendingCheckMilliseconds = 3000;

const libraryPath = "/admin/knowledge";

/**
 * One Knowledge document's page: its details (editable), status and why it
 * failed, Replace file, the text Zeph draws on in the Knowledge text editor
 * (editable), Retry when it failed and Delete. Checks again every few
 * seconds while the document is pending.
 *
 * @param props - `documentId` is the document to show.
 * @returns The page body, or a loading, not-found or error state.
 */
export function KnowledgeDocumentView({ documentId }: { documentId: string }) {
  const apiClient = useApiClient();
  const router = useRouter();
  const queryClient = useQueryClient();
  const documentKey = queryKeys.knowledgeDocument(documentId);

  const documentQuery = useQuery({
    queryKey: documentKey,
    queryFn: () => apiClient.getKnowledgeDocument(documentId),
    refetchInterval: (query) =>
      query.state.data?.status === "pending" ? pendingCheckMilliseconds : false,
  });
  const isNotFound =
    documentQuery.error instanceof ApiError &&
    documentQuery.error.status === 404;

  function showSaved(saved: KnowledgeDocumentWithText) {
    queryClient.setQueryData(documentKey, saved);
    void queryClient.invalidateQueries({
      queryKey: queryKeys.knowledgeDocuments,
    });
    return saved;
  }

  async function saveDetails(
    knowledgeDocument: KnowledgeDocumentWithText,
    change: KnowledgeDetailsChange,
  ) {
    return showSaved(
      await apiClient.updateKnowledgeDocumentDetails(
        knowledgeDocument.id,
        change,
      ),
    );
  }

  async function saveText(text: string) {
    return showSaved(
      await apiClient.saveKnowledgeDocumentText(documentId, text),
    );
  }

  async function replaceFile(file: File) {
    return showSaved(
      await apiClient.replaceKnowledgeDocumentFile(documentId, file),
    );
  }

  const retryDocument = useMutation({
    mutationFn: async () => {
      await apiClient.retryKnowledgeDocument(documentId);
      void queryClient.invalidateQueries({
        queryKey: queryKeys.knowledgeDocuments,
      });
      await queryClient.invalidateQueries({ queryKey: documentKey });
    },
  });

  const deleteDocument = useMutation({
    mutationFn: () => apiClient.deleteKnowledgeDocument(documentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.knowledgeDocuments,
      });
      router.push(libraryPath);
    },
  });

  const isBusy =
    retryDocument.isPending ||
    deleteDocument.isPending ||
    deleteDocument.isSuccess;

  function remove(knowledgeDocument: KnowledgeDocumentWithText) {
    if (
      window.confirm(
        `Delete ${knowledgeDocument.title}? Zeph will stop drawing on it.`,
      )
    ) {
      retryDocument.reset();
      deleteDocument.mutate();
    }
  }

  const backLink = (
    <Link href={libraryPath} className="w-fit text-sm font-medium">
      ← Knowledge
    </Link>
  );

  if (documentQuery.isPending) {
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

  if (!documentQuery.data && isNotFound) {
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

  if (!documentQuery.data) {
    return (
      <div className="flex flex-col gap-9">
        {backLink}
        <LoadFailed
          title="Couldn’t load the document"
          body="Zeph keeps using documents that are already Ready."
          onRetry={() => void documentQuery.refetch()}
        />
      </div>
    );
  }

  const knowledgeDocument = documentQuery.data;

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

      {retryDocument.isError || deleteDocument.isError ? (
        <p
          role="status"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          Couldn’t {retryDocument.isError ? "retry" : "delete"}{" "}
          {knowledgeDocument.title}. Please try again.
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
            onClick={() => {
              deleteDocument.reset();
              retryDocument.mutate();
            }}
          >
            Retry
          </button>
        </div>
      ) : null}

      <KnowledgeDetailsForm
        knowledgeDocument={knowledgeDocument}
        onSave={(change) => saveDetails(knowledgeDocument, change)}
      />

      <KnowledgeReplaceFileForm
        knowledgeDocument={knowledgeDocument}
        onReplace={replaceFile}
      />

      <KnowledgeTextSection
        knowledgeDocument={knowledgeDocument}
        onSave={saveText}
      />

      <div className="flex flex-col items-start gap-2 border-t border-line pt-6">
        <button
          type="button"
          className={dangerButton}
          disabled={isBusy}
          onClick={() => remove(knowledgeDocument)}
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
