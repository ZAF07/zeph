"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { UserPortrait } from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The "About you" tab, headed "What I know about you": Zeph's User Portrait
 * of the User and when it was last written. It can be deleted, but not
 * edited.
 *
 * @param props - `portrait` is the User's Portrait, or null if they have
 *   none, `copy` is the Memories page's Copy, and `timeZone` is the User's
 *   time zone.
 * @returns The tab's content.
 */
export function UserPortraitSection({
  portrait,
  copy,
  timeZone,
}: {
  portrait: UserPortrait | null;
  copy: Copy;
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
        title={readCopy(copy, "memories.about.heading")}
        body={readCopy(copy, "memories.about.lead")}
      />

      {deletePortrait.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {portrait ? (
        <MemoryCard
          deleteLabel={readCopy(copy, "memories.about.delete")}
          isDeleting={deletePortrait.isPending}
          onDelete={() => deletePortrait.mutate()}
        >
          <div className="min-w-0">
            <p className="mt-0 mb-2 text-[15px] whitespace-pre-line text-text">
              {portrait.text}
            </p>
            <span className="text-[12px] text-soft">
              {fillCopy(copy, "memories.about.written", {
                day: formatShortDay(portrait.updated_at, timeZone),
              })}
            </span>
          </div>
        </MemoryCard>
      ) : (
        <EmptyState
          title={readCopy(copy, "memories.about.empty_title")}
          body={readCopy(copy, "memories.about.empty_body")}
        />
      )}
    </>
  );
}
