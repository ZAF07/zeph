"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { KnowledgeDocumentCard } from "@/components/KnowledgeDocumentCard";
import { KnowledgeUploadBox } from "@/components/KnowledgeUploadBox";
import { LoadFailed } from "@/components/LoadFailed";
import type { KnowledgeDocument, KnowledgeUpload } from "@/lib/api-client";
import { formatAddedDay } from "@/lib/dates";
import { knowledgeStatusOrder } from "@/lib/knowledge-labels";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const pendingCheckMilliseconds = 3000;

/**
 * Writes how many documents there are of each status, like " · 4 ready ·
 * 1 failed", for after the document count.
 *
 * @param documents - Every document in the library.
 * @returns The count of each status there is, each after a " · ".
 */
function statusCounts(documents: KnowledgeDocument[]): string {
  return knowledgeStatusOrder
    .map((status) => ({
      status,
      count: documents.filter(
        (knowledgeDocument) => knowledgeDocument.status === status,
      ).length,
    }))
    .filter(({ count }) => count > 0)
    .map(({ status, count }) => ` · ${count} ${status}`)
    .join("");
}

/**
 * The admin Knowledge library, from the card-list template: a folding card
 * per document showing its status while it is indexed, with Open document,
 * Retry for one that failed, and Delete; and the "Add a document" box above
 * the list. Checks again every few seconds while any document is pending.
 *
 * @returns The library, or a loading, empty or error state.
 */
export function KnowledgeLibrary() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);

  const documentsQuery = useQuery({
    queryKey: queryKeys.knowledgeDocuments,
    queryFn: () => apiClient.listKnowledgeDocuments(),
    refetchInterval: (query) =>
      query.state.data?.some(
        (knowledgeDocument) => knowledgeDocument.status === "pending",
      )
        ? pendingCheckMilliseconds
        : false,
  });
  const documents = documentsQuery.data;

  async function reloadDocuments() {
    await queryClient.invalidateQueries({
      queryKey: queryKeys.knowledgeDocuments,
    });
  }

  async function upload(newDocument: KnowledgeUpload) {
    setFlash(null);
    const uploaded = await apiClient.uploadKnowledgeDocument(newDocument);
    setIsAdding(false);
    setFlash({
      text: `Uploaded ${uploaded.title}. It’s being indexed now.`,
      isError: false,
    });
    await reloadDocuments();
  }

  const change = useMutation({
    mutationFn: async ({
      action,
    }: {
      target: KnowledgeDocument;
      action: () => Promise<unknown>;
      successText: string | null;
    }) => {
      await action();
      await reloadDocuments();
    },
    onMutate: () => setFlash(null),
    onSuccess: (_, { successText }) => {
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
    },
    onError: (_, { target }) =>
      setFlash({
        text: `Couldn’t change ${target.title}. Please try again.`,
        isError: true,
      }),
  });
  const changingId = change.isPending ? change.variables.target.id : null;

  if (!documents) {
    if (documentsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load the document list"
          body="Zeph keeps using documents that are already Ready."
          onRetry={() => void documentsQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading documents" />;
  }

  const now = new Date();

  return (
    <CardList
      items={documents}
      count={
        <>
          <CardCount
            count={documents.length}
            words={documents.length === 1 ? "document" : "documents"}
          />
          {statusCounts(documents)}
        </>
      }
      addLabel="Add a document"
      onAdd={() => {
        setIsAdding(true);
        setFlash(null);
      }}
      isAddDisabled={isAdding}
      aboveList={
        <>
          <CardListFlash flash={flash} />
          {isAdding ? (
            <KnowledgeUploadBox
              onUpload={upload}
              onCancel={() => setIsAdding(false)}
            />
          ) : null}
          {documents.length === 0 ? (
            <EmptyState
              title="The library is empty"
              body="Until you add documents, Zeph relies on general knowledge only. Start with a few primary texts per tradition."
            />
          ) : null}
        </>
      }
      renderCard={(knowledgeDocument, _index, folding) => (
        <KnowledgeDocumentCard
          key={knowledgeDocument.id}
          knowledgeDocument={knowledgeDocument}
          addedDay={formatAddedDay(knowledgeDocument.created_at, now)}
          isOpen={folding.isOpen}
          onToggle={folding.onToggle}
          onRetry={() =>
            change.mutate({
              target: knowledgeDocument,
              action: () =>
                apiClient.retryKnowledgeDocument(knowledgeDocument.id),
              successText: null,
            })
          }
          onDelete={() =>
            change.mutate({
              target: knowledgeDocument,
              action: () =>
                apiClient.deleteKnowledgeDocument(knowledgeDocument.id),
              successText: `Deleted ${knowledgeDocument.title}.`,
            })
          }
          isChanging={changingId === knowledgeDocument.id}
        />
      )}
    />
  );
}
