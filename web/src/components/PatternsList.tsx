"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { Pattern } from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { formatShortCalendarDay, formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Patterns tab: each Pattern the User agreed with, newest agreed first,
 * with the day they agreed and what it is based on (one line per piece of
 * evidence: the day, its Life Thread and what happened); each can be
 * deleted, so Zeph stops using it.
 *
 * @param props - `patterns` are the User's confirmed Patterns, newest
 *   agreed first, `copy` is the Memories page's Copy, and `timeZone` is the
 *   User's time zone.
 * @returns The tab's content.
 */
export function PatternsList({
  patterns,
  copy,
  timeZone,
}: {
  patterns: Pattern[];
  copy: Copy;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deletePattern = useMutation({
    mutationFn: (patternId: string) => apiClient.deletePattern(patternId),
    onSuccess: (_, patternId) =>
      queryClient.setQueryData(
        queryKeys.patterns,
        patterns.filter((pattern) => pattern.id !== patternId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title={readCopy(copy, "memories.patterns.heading")}
        body={readCopy(copy, "memories.patterns.lead")}
      />

      {deletePattern.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {patterns.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-6 p-0">
          {patterns.map((pattern) => (
            <li key={pattern.id}>
              <MemoryCard
                deleteLabel={fillCopy(copy, "memories.patterns.delete", {
                  pattern: pattern.pattern,
                })}
                isDeleting={deletePattern.isPending}
                onDelete={() => deletePattern.mutate(pattern.id)}
                below={
                  <div className="mt-3.5 pr-2.5">
                    <div className="pb-2 text-[11px] font-medium tracking-[2px] text-soft uppercase">
                      {readCopy(copy, "memories.patterns.based_on")}
                    </div>
                    {pattern.evidence.map((item, index) => (
                      <div
                        key={index}
                        className="flex flex-wrap gap-x-4 gap-y-0.5 border-t border-line py-2.5"
                      >
                        <span className="flex-[0_0_190px] text-[13px] text-soft">
                          {fillCopy(copy, "memories.patterns.evidence_when", {
                            day: formatShortCalendarDay(item.day),
                            thread: item.thread,
                          })}
                        </span>
                        <span className="min-w-0 flex-[1_1_260px] text-[14px] text-text">
                          {item.line}
                        </span>
                      </div>
                    ))}
                  </div>
                }
              >
                <div className="min-w-0">
                  <p className="m-0 text-[16px] font-normal text-text">
                    {pattern.pattern}
                  </p>
                  <div className="mt-1.5">
                    <span className="text-[12px] text-soft">
                      {fillCopy(copy, "memories.patterns.agreed", {
                        day: formatShortDay(pattern.agreed_at, timeZone),
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
          title={readCopy(copy, "memories.patterns.empty_title")}
          body={readCopy(copy, "memories.patterns.empty_body")}
        />
      )}
    </>
  );
}
