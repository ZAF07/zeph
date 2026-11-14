"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  confirmDangerButton,
  dangerButton,
  deleteIconButton,
  secondaryButton,
} from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import type { MemoryGroup } from "@/lib/api-client";
import { memorySourceLabel } from "@/lib/memories";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Memories tab: Memory Items grouped by Memory Category, each deletable,
 * and "Delete all memories" with a confirm step.
 *
 * @param props - `groups` are the User's Memory Items by category, and
 *   `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function MemoryItemsList({
  groups,
  timeZone,
}: {
  groups: MemoryGroup[];
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isConfirmingDeleteAll, setIsConfirmingDeleteAll] = useState(false);
  const memoryCount = groups.reduce(
    (count, group) => count + group.items.length,
    0,
  );

  function showGroupsLeft(groupsLeft: MemoryGroup[]) {
    queryClient.setQueryData(queryKeys.memoryGroups, groupsLeft);
    void queryClient.invalidateQueries({ queryKey: queryKeys.home });
  }

  const deleteItem = useMutation({
    mutationFn: (itemId: string) => apiClient.deleteMemoryItem(itemId),
    onSuccess: (_, itemId) =>
      showGroupsLeft(
        groups
          .map((group) => ({
            ...group,
            items: group.items.filter((item) => item.id !== itemId),
          }))
          .filter((group) => group.items.length > 0),
      ),
  });

  const deleteAll = useMutation({
    mutationFn: () => apiClient.deleteAllMemoryItems(),
    onSuccess: () => {
      setIsConfirmingDeleteAll(false);
      showGroupsLeft([]);
    },
  });

  const isDeleting = deleteItem.isPending || deleteAll.isPending;
  const deleteFailed = deleteItem.isError || deleteAll.isError;

  return (
    <div className="flex flex-col gap-[42px]">
      {memoryCount > 0 ? (
        <p className="m-0 text-caption text-ink-muted">
          {memoryCount} {memoryCount === 1 ? "memory" : "memories"}, grouped by
          category
        </p>
      ) : null}

      {deleteFailed ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {groups.map((group) => (
        <section
          key={group.category}
          aria-label={group.category}
          className="flex flex-col gap-2.5"
        >
          <h2 className="m-0 flex items-baseline gap-2 text-[15px] font-semibold">
            {group.category}
            <span className="text-caption font-normal text-ink-muted">
              {group.items.length}
            </span>
          </h2>
          <ul className="m-0 list-none overflow-hidden rounded-card border border-line bg-white p-0">
            {group.items.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-center gap-3 border-t border-line py-3.5 pr-3 pl-6 first:border-t-0"
              >
                <span className="flex min-w-0 flex-auto flex-col gap-1">
                  <span className="text-base">{item.content}</span>
                  <span className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center whitespace-nowrap rounded-full bg-code px-2.5 py-[3px] text-xs font-medium text-ink-body">
                      {group.category}
                    </span>
                    <span className="text-caption text-ink-muted">
                      {memorySourceLabel(item, timeZone)}
                    </span>
                  </span>
                </span>
                <button
                  type="button"
                  aria-label={`Delete memory: ${item.content}`}
                  className={deleteIconButton}
                  disabled={isDeleting}
                  onClick={() => {
                    deleteAll.reset();
                    deleteItem.mutate(item.id);
                  }}
                >
                  <DeleteIcon />
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}

      {memoryCount === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            Zeph hasn’t remembered anything yet
          </span>
          <p className="m-0 max-w-[32em] text-caption text-ink-muted">
            As you talk, meaningful details — goals, what helps, people you
            mention — will appear here, grouped by category.
          </p>
          <a href="https://t.me/" className={secondaryButton}>
            Open Telegram
          </a>
        </div>
      ) : (
        <section
          aria-labelledby="delete-all-memories"
          className="flex flex-col gap-3 rounded-card border border-danger-line p-6"
        >
          <h2
            id="delete-all-memories"
            className="m-0 text-[17px] font-semibold text-danger"
          >
            Delete all memories
          </h2>
          <p className="m-0 text-[15px] text-ink-soft">
            Removes every memory. Conversation Summaries and your account stay.
            This can’t be undone.
          </p>
          {isConfirmingDeleteAll ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">
                Delete all {memoryCount}{" "}
                {memoryCount === 1 ? "memory" : "memories"}?
              </span>
              <button
                type="button"
                className={confirmDangerButton}
                disabled={isDeleting}
                onClick={() => {
                  deleteItem.reset();
                  deleteAll.mutate();
                }}
              >
                Yes, delete all
              </button>
              <button
                type="button"
                className={secondaryButton}
                onClick={() => setIsConfirmingDeleteAll(false)}
              >
                Keep them
              </button>
            </div>
          ) : (
            <button
              type="button"
              className={`${dangerButton} self-start`}
              onClick={() => setIsConfirmingDeleteAll(true)}
            >
              Delete all memories
            </button>
          )}
        </section>
      )}
    </div>
  );
}
