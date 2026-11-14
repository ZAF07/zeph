"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import type { ConversationSummary } from "@/lib/api-client";
import { formatWeekdayDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Conversation Summaries tab: a read-only list by date, newest first,
 * with how the User seemed; each summary can be deleted.
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
    <div className="flex flex-col gap-6">
      <p className="m-0 text-caption text-ink-muted">
        After each Conversation, Zeph writes a short note so it can pick up
        where you left off. These stay until you delete them.
      </p>

      {deleteSummary.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {summaries.length > 0 ? (
        <ol className="m-0 flex list-none flex-col gap-3 p-0">
          {summaries.map((summary) => {
            const day = formatWeekdayDay(summary.created_at, timeZone);
            return (
              <li
                key={summary.id}
                className="flex items-start gap-4 rounded-card border border-line bg-white py-5 pr-5 pl-6"
              >
                <span className="flex min-w-0 flex-auto flex-col gap-2">
                  <span className="text-caption font-semibold text-ink-body">
                    {day}
                  </span>
                  <span className="text-[15px]">{summary.summary}</span>
                  <span className="inline-flex items-center gap-2 text-caption text-ink-soft">
                    <span
                      aria-hidden="true"
                      className="size-2 rounded-full bg-blue opacity-50"
                    />
                    You seemed {summary.mood}
                  </span>
                  {summary.offered ? (
                    <span className="text-caption text-ink-soft">
                      {summary.offered}
                    </span>
                  ) : null}
                </span>
                <button
                  type="button"
                  aria-label={`Delete summary from ${day}`}
                  className={deleteIconButton}
                  disabled={deleteSummary.isPending}
                  onClick={() => deleteSummary.mutate(summary.id)}
                >
                  <DeleteIcon />
                </button>
              </li>
            );
          })}
        </ol>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No Conversation Summaries yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            They appear a little while after a Conversation ends.
          </p>
        </div>
      )}
    </div>
  );
}
