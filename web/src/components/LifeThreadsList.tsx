"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { filledPill, outlinedPill } from "@/components/card-styles";
import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { LifeThread } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The "What's going on in your life" tab: each Life Thread's story, whether
 * it is open or closed and when it was last updated, open ones first; each
 * can be deleted, so Zeph never brings it up again.
 *
 * @param props - `threads` are the User's Life Threads, open first, and
 *   `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function LifeThreadsList({
  threads,
  timeZone,
}: {
  threads: LifeThread[];
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deleteThread = useMutation({
    mutationFn: (threadId: string) => apiClient.deleteLifeThread(threadId),
    onSuccess: (_, threadId) =>
      queryClient.setQueryData(
        queryKeys.lifeThreads,
        threads.filter((thread) => thread.id !== threadId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title="What's going on in your life"
        body="The ongoing stories Zeph follows, so it can ask how things went. Delete one and Zeph won't bring it up again."
      />

      {deleteThread.isError ? (
        <SaveFailedNote>
          We couldn’t delete that. Please try again.
        </SaveFailedNote>
      ) : null}

      {threads.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-6 p-0">
          {threads.map((thread) => (
            <li key={thread.id}>
              <MemoryCard
                deleteLabel={`Delete story: ${thread.title}`}
                isDeleting={deleteThread.isPending}
                onDelete={() => deleteThread.mutate(thread.id)}
                roomy={false}
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-[16px] font-normal text-text">
                      {thread.title}
                    </span>
                    <span
                      className={thread.is_open ? filledPill : outlinedPill}
                    >
                      {thread.is_open ? "Open" : "Closed"}
                    </span>
                  </div>
                  <p className="mt-2 mb-1.5 text-[14px] text-soft">
                    {thread.story}
                  </p>
                  <span className="text-[12px] text-soft">
                    {`Updated ${formatShortDay(thread.updated_at, timeZone)}`}
                  </span>
                </div>
              </MemoryCard>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title="Nothing here yet"
          body="When you tell Zeph about something ongoing, it appears here a little while after the Conversation ends."
        />
      )}
    </>
  );
}
