"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { filledPill, outlinedPill } from "@/components/card-styles";
import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { MemoryCard } from "@/components/MemoryCard";
import { MemoryDetailLine } from "@/components/MemoryDetailLine";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { MoveOutcome } from "@/lib/api-client";
import { type Copy, fillPlaceholders, readCopy } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const resultSlots: Record<MoveOutcome["result"], string> = {
  helped: "memories.helps.helped",
  didnt_help: "memories.helps.didnt_help",
  mixed: "memories.helps.mixed",
};

/**
 * The "What helps you" tab: each Move Outcome, newest first, with the kind
 * of help, whether it helped, when it was used, how the User felt, why and
 * the day; each can be deleted, so Zeph never uses it again.
 *
 * @param props - `outcomes` are the User's Move Outcomes, newest first,
 *   `copy` is the Memories page's Copy, and `timeZone` is the User's time
 *   zone.
 * @returns The tab's content.
 */
export function MoveOutcomesList({
  outcomes,
  copy,
  timeZone,
}: {
  outcomes: MoveOutcome[];
  copy: Copy;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deleteOutcome = useMutation({
    mutationFn: (outcomeId: string) => apiClient.deleteMoveOutcome(outcomeId),
    onSuccess: (_, outcomeId) =>
      queryClient.setQueryData(
        queryKeys.moveOutcomes,
        outcomes.filter((outcome) => outcome.id !== outcomeId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title={readCopy(copy, "memories.helps.heading")}
        body={readCopy(copy, "memories.helps.lead")}
      />

      {deleteOutcome.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {outcomes.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-6 p-0">
          {outcomes.map((outcome) => {
            const day = formatShortDay(outcome.made_at, timeZone);
            return (
              <li key={outcome.id}>
                <MemoryCard
                  deleteLabel={fillPlaceholders(
                    readCopy(copy, "memories.helps.delete"),
                    { help: outcome.move, day },
                  )}
                  isDeleting={deleteOutcome.isPending}
                  onDelete={() => deleteOutcome.mutate(outcome.id)}
                >
                  <div className="flex min-w-0 flex-col gap-1.5">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="text-[16px] font-normal text-text">
                        {outcome.move}
                      </span>
                      <span
                        className={
                          outcome.result === "helped"
                            ? filledPill
                            : outlinedPill
                        }
                      >
                        {readCopy(copy, resultSlots[outcome.result])}
                      </span>
                    </div>
                    <MemoryDetailLine
                      label={readCopy(copy, "memories.helps.when")}
                    >
                      {outcome.situation}
                    </MemoryDetailLine>
                    <MemoryDetailLine
                      label={readCopy(copy, "memories.helps.feeling")}
                    >
                      {outcome.feeling}
                    </MemoryDetailLine>
                    <MemoryDetailLine
                      label={readCopy(copy, "memories.helps.why")}
                    >
                      {outcome.why}
                    </MemoryDetailLine>
                    <span className="text-[12px] text-soft">{day}</span>
                  </div>
                </MemoryCard>
              </li>
            );
          })}
        </ul>
      ) : (
        <EmptyState
          title={readCopy(copy, "memories.helps.empty_title")}
          body={readCopy(copy, "memories.helps.empty_body")}
        />
      )}
    </>
  );
}
