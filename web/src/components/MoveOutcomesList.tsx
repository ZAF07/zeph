"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import type { MoveOutcome } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const resultLabels: Record<MoveOutcome["result"], string> = {
  helped: "Helped",
  didnt_help: "Didn’t help",
  mixed: "Mixed",
};

const resultStyles: Record<MoveOutcome["result"], string> = {
  helped: "bg-blue-tint text-blue-deep",
  didnt_help: "bg-code text-ink-body",
  mixed: "bg-code text-ink-body",
};

/**
 * The "What helps you" tab: each Move Outcome, newest first, with the kind
 * of help, whether it helped, the situation, how the User felt, why and the
 * day; each can be deleted, so Zeph never uses it again.
 *
 * @param props - `outcomes` are the User's Move Outcomes, newest first, and
 *   `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function MoveOutcomesList({
  outcomes,
  timeZone,
}: {
  outcomes: MoveOutcome[];
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
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h2 className="m-0 text-[15px] font-semibold">What helps you</h2>
        <p className="m-0 text-caption text-ink-muted">
          What Zeph learned about the kinds of help that work for you, and when.
          Delete one and Zeph won’t use it again.
        </p>
      </div>

      {deleteOutcome.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {outcomes.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {outcomes.map((outcome) => {
            const day = formatShortDay(outcome.made_at, timeZone);
            return (
              <li
                key={outcome.id}
                className="flex items-start gap-4 rounded-card border border-line bg-white py-5 pr-5 pl-6"
              >
                <span className="flex min-w-0 flex-auto flex-col gap-2">
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="text-[15px] font-semibold">
                      {outcome.move}
                    </span>
                    <span
                      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium ${resultStyles[outcome.result]}`}
                    >
                      {resultLabels[outcome.result]}
                    </span>
                  </span>
                  <span className="text-[15px]">{outcome.situation}</span>
                  <span className="text-[15px] text-ink-soft">
                    {`You felt ${outcome.feeling}`}
                  </span>
                  <span className="text-[15px]">{outcome.why}</span>
                  <span className="text-caption text-ink-muted">{day}</span>
                </span>
                <button
                  type="button"
                  aria-label={`Delete what helps: ${outcome.move}, ${day}`}
                  className={deleteIconButton}
                  disabled={deleteOutcome.isPending}
                  onClick={() => deleteOutcome.mutate(outcome.id)}
                >
                  <DeleteIcon />
                </button>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            Nothing here yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            When Zeph helps you in a chat, what it learned appears here a little
            while after the Conversation ends.
          </p>
        </div>
      )}
    </div>
  );
}
