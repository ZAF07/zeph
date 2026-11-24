"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { KeptQuote } from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { formatShortCalendarDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Things you said tab: each quote Zeph keeps as evidence, newest day
 * first, with the day it was said and Zeph's note on what was going on,
 * shown apart from the quote. No Pattern is named. Each can be deleted, so
 * Zeph stops using it.
 *
 * @param props - `quotes` are the User's kept quotes, newest day first, and
 *   `copy` is the Memories page's Copy.
 * @returns The tab's content.
 */
export function KeptQuotesList({
  quotes,
  copy,
}: {
  quotes: KeptQuote[];
  copy: Copy;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deleteQuote = useMutation({
    mutationFn: (quoteId: string) => apiClient.deleteKeptQuote(quoteId),
    onSuccess: (_, quoteId) =>
      queryClient.setQueryData(
        queryKeys.keptQuotes,
        quotes.filter((quote) => quote.id !== quoteId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title={readCopy(copy, "memories.quotes.heading")}
        body={readCopy(copy, "memories.quotes.lead")}
      />

      {deleteQuote.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {quotes.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-6 p-0">
          {quotes.map((quote) => (
            <li key={quote.id}>
              <MemoryCard
                deleteLabel={fillCopy(copy, "memories.quotes.delete", {
                  quote: quote.quote,
                })}
                isDeleting={deleteQuote.isPending}
                onDelete={() => deleteQuote.mutate(quote.id)}
                below={
                  <div className="mt-3.5 pr-2.5">
                    <div className="pb-2 text-[11px] font-medium tracking-[2px] text-soft uppercase">
                      {readCopy(copy, "memories.quotes.note_label")}
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-0.5 border-t border-line py-2.5">
                      <span className="min-w-0 flex-[1_1_260px] text-[14px] text-text">
                        {quote.context}
                      </span>
                    </div>
                  </div>
                }
              >
                <div className="min-w-0">
                  <p className="m-0 text-[16px] font-normal text-text">
                    {fillCopy(copy, "memories.quotes.quote", {
                      quote: quote.quote,
                    })}
                  </p>
                  <div className="mt-1.5">
                    <span className="text-[12px] text-soft">
                      {fillCopy(copy, "memories.quotes.said_on", {
                        day: formatShortCalendarDay(quote.day),
                      })}
                    </span>
                  </div>
                </div>
              </MemoryCard>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title={readCopy(copy, "memories.quotes.empty_title")}
          body={readCopy(copy, "memories.quotes.empty_body")}
        />
      )}
    </>
  );
}
