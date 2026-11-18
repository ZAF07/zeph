"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { UserPortrait } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The "About you" tab, headed "What I know about you": Zeph's User Portrait
 * of the User and when it was last written. It can be deleted, but not
 * edited.
 *
 * @param props - `portrait` is the User's Portrait, or null if they have
 *   none, and `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function UserPortraitSection({
  portrait,
  timeZone,
}: {
  portrait: UserPortrait | null;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deletePortrait = useMutation({
    mutationFn: () => apiClient.deleteUserPortrait(),
    onSuccess: () => queryClient.setQueryData(queryKeys.userPortrait, null),
  });

  return (
    <>
      <MemoriesPanelHeading
        title="What I know about you"
        body="Zeph's short picture of you, written from your memories, so every reply comes from knowing you. Delete it and Zeph stops using it; it is written again after a later Conversation, while Memory is on."
      />

      {deletePortrait.isError ? (
        <SaveFailedNote>
          We couldn’t delete that. Please try again.
        </SaveFailedNote>
      ) : null}

      {portrait ? (
        <MemoryCard
          deleteLabel="Delete what Zeph knows about you"
          isDeleting={deletePortrait.isPending}
          onDelete={() => deletePortrait.mutate()}
        >
          <div className="min-w-0">
            <p className="mt-0 mb-2 text-[15px] whitespace-pre-line text-text">
              {portrait.text}
            </p>
            <span className="text-[12px] text-soft">
              {`Written ${formatShortDay(portrait.updated_at, timeZone)}`}
            </span>
          </div>
        </MemoryCard>
      ) : (
        <EmptyState
          title="Nothing here yet"
          body="Zeph writes this a little while after a Conversation ends, while Memory is on."
        />
      )}
    </>
  );
}
