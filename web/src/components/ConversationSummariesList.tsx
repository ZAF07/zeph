"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { MemoryDetailLine } from "@/components/MemoryDetailLine";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { ConversationSummary } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Conversation Summaries tab: a read-only list by date, newest first,
 * with how the User seemed and what Zeph offered; each summary can be
 * deleted.
 *
 * @param props - `summaries` are the User's Conversation Summaries, newest
 *   first, and `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function ConversationSummariesList({
  summaries,
  timeZone,
}: {
  summaries: ConversationSummary[];
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deleteSummary = useMutation({
    mutationFn: (summaryId: string) =>
      apiClient.deleteConversationSummary(summaryId),
    onSuccess: (_, summaryId) =>
      queryClient.setQueryData(
        queryKeys.conversationSummaries,
        summaries.filter((item) => item.id !== summaryId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title="Conversation Summaries"
        body="After each Conversation, Zeph writes a short note so it can pick up where you left off. These stay until you delete them."
      />

      {deleteSummary.isError ? (
        <SaveFailedNote>
          We couldn’t delete that. Please try again.
        </SaveFailedNote>
      ) : null}

      {summaries.length > 0 ? (
        <ol className="m-0 flex list-none flex-col gap-6 p-0">
          {summaries.map((summary) => {
            const day = formatShortDay(summary.created_at, timeZone);
            return (
              <li key={summary.id}>
                <MemoryCard
                  deleteLabel={`Delete summary from ${day}`}
                  isDeleting={deleteSummary.isPending}
                  onDelete={() => deleteSummary.mutate(summary.id)}
                >
                  <div className="flex min-w-0 flex-col gap-1.5">
                    <p className="m-0 text-[15px] text-text">
                      {summary.summary}
                    </p>
                    <MemoryDetailLine label="Seemed">
                      {summary.mood}
                    </MemoryDetailLine>
                    {summary.offered ? (
                      <MemoryDetailLine label="Zeph offered">
                        {summary.offered}
                      </MemoryDetailLine>
                    ) : null}
                    <span className="text-[12px] text-soft">{day}</span>
                  </div>
                </MemoryCard>
              </li>
            );
          })}
        </ol>
      ) : (
        <EmptyState
          title="No Conversation Summaries yet"
          body="They appear a little while after a Conversation ends."
        />
      )}
    </>
  );
}
