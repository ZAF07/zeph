"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import type { UserPortrait } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The "What I know about you" tab: Zeph's User Portrait of the User and when
 * it was last written. It can be deleted, but not edited.
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
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h2 className="m-0 text-[15px] font-semibold">What I know about you</h2>
        <p className="m-0 text-caption text-ink-muted">
          Zeph’s short picture of you, written from your memories, so every
          reply comes from knowing you. Delete it and Zeph stops using it; it is
          written again after a later Conversation, while Memory is on.
        </p>
      </div>

      {deletePortrait.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {portrait ? (
        <div className="flex items-start gap-4 rounded-card border border-line bg-white py-5 pr-5 pl-6">
          <span className="flex min-w-0 flex-auto flex-col gap-2">
            <span className="whitespace-pre-line text-[15px]">
              {portrait.text}
            </span>
            <span className="text-caption text-ink-muted">
              {`Updated ${formatShortDay(portrait.updated_at, timeZone)}`}
            </span>
          </span>
          <button
            type="button"
            aria-label="Delete what Zeph knows about you"
            className={deleteIconButton}
            disabled={deletePortrait.isPending}
            onClick={() => deletePortrait.mutate()}
          >
            <DeleteIcon />
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            Nothing here yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            Zeph writes this a little while after a Conversation ends, while
            Memory is on.
          </p>
        </div>
      )}
    </div>
  );
}
