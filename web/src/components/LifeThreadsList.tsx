"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import type { LifeThread } from "@/lib/api-client";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The "What's going on in your life" tab: each Life Thread's story, whether
 * it is open or settled and when it was last updated, open ones first; each
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
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1.5">
        <h2 className="m-0 text-[15px] font-semibold">
          What’s going on in your life
        </h2>
        <p className="m-0 text-caption text-ink-muted">
          The ongoing stories Zeph follows, so it can ask how things went.
          Delete one and Zeph won’t bring it up again.
        </p>
      </div>

      {deleteThread.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {threads.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {threads.map((thread) => (
            <li
              key={thread.id}
              className="flex items-start gap-4 rounded-card border border-line bg-white py-5 pr-5 pl-6"
            >
              <span className="flex min-w-0 flex-auto flex-col gap-2">
                <span className="flex flex-wrap items-center gap-2">
                  <span className="text-[15px] font-semibold">
                    {thread.title}
                  </span>
                  <span className="inline-flex items-center whitespace-nowrap rounded-full bg-code px-2.5 py-[3px] text-xs font-medium text-ink-body">
                    {thread.is_open ? "Open" : "Settled"}
                  </span>
                </span>
                <span className="text-[15px]">{thread.story}</span>
                <span className="text-caption text-ink-muted">
                  {`Updated ${formatShortDay(thread.updated_at, timeZone)}`}
                </span>
              </span>
              <button
                type="button"
                aria-label={`Delete story: ${thread.title}`}
                className={deleteIconButton}
                disabled={deleteThread.isPending}
                onClick={() => deleteThread.mutate(thread.id)}
              >
                <DeleteIcon />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            Nothing here yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            When you tell Zeph about something ongoing, it appears here a little
            while after the Conversation ends.
          </p>
        </div>
      )}
    </div>
  );
}
