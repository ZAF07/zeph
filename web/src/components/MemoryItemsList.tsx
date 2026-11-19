"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { dangerButton, deleteIconButton } from "@/components/button-styles";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DeleteIcon } from "@/components/DeleteIcon";
import { EmptyState } from "@/components/EmptyState";
import { PillLink } from "@/components/PillLink";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { MemoryGroup } from "@/lib/api-client";
import { type Copy, countSlotKey, fillCopy, readCopy } from "@/lib/copy";
import { memorySourceLabel } from "@/lib/memories";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Memories tab: Memory Items grouped by Memory Category, each deletable,
 * and "Delete all memories", which asks first, worded for one memory or several.
 *
 * @param props - `groups` are the User's Memory Items by category, `copy`
 *   is the Memories page's Copy, and `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function MemoryItemsList({
  groups,
  copy,
  timeZone,
}: {
  groups: MemoryGroup[];
  copy: Copy;
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
    onSuccess: () => showGroupsLeft([]),
  });

  const isDeleting = deleteItem.isPending || deleteAll.isPending;
  const deleteFailed = deleteItem.isError || deleteAll.isError;

  return (
    <>
      {deleteFailed ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {groups.map((group) => (
        <section key={group.category} aria-label={group.category}>
          <h3 className="mt-0 mb-2 text-[12px] font-medium tracking-[2px] text-soft uppercase">
            {group.category}
          </h3>
          <ul className="m-0 box-border list-none rounded-card border border-line bg-panel px-[22px] py-1.5 [overflow-wrap:anywhere]">
            {group.items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-3 border-t border-line py-2 first:border-t-0"
              >
                <div className="min-w-0">
                  <div className="text-[15px] text-text">{item.content}</div>
                  <div className="text-[12px] text-soft">
                    {memorySourceLabel(item, copy, timeZone)}
                  </div>
                </div>
                <button
                  type="button"
                  aria-label={fillCopy(copy, "memories.items.delete", {
                    memory: item.content,
                  })}
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
        <EmptyState
          title={readCopy(copy, "memories.items.empty_title")}
          body={readCopy(copy, "memories.items.empty_body")}
          action={
            <PillLink
              href="https://t.me/"
              label={readCopy(copy, "memories.items.empty_link")}
            />
          }
        />
      ) : (
        <section
          aria-labelledby="delete-all-memories"
          className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-t border-line pt-5"
        >
          <div className="flex-[1_1_320px]">
            <h2
              id="delete-all-memories"
              className="m-0 text-[17px] font-normal text-cream"
            >
              {readCopy(copy, "memories.items.delete_all.heading")}
            </h2>
            <p className="mt-1 mb-0 text-[14px] text-soft">
              {readCopy(copy, "memories.items.delete_all.body")}
            </p>
          </div>
          <button
            type="button"
            className={dangerButton}
            disabled={isDeleting}
            onClick={() => setIsConfirmingDeleteAll(true)}
          >
            {readCopy(copy, "memories.items.delete_all.button")}
          </button>
        </section>
      )}

      <ConfirmDialog
        open={isConfirmingDeleteAll}
        title={readCopy(copy, "memories.items.delete_all.confirm_title")}
        body={readCopy(
          copy,
          countSlotKey("memories.items.delete_all.confirm_body", memoryCount),
        )}
        cancelLabel={readCopy(copy, "memories.items.delete_all.keep")}
        confirmLabel={readCopy(copy, "memories.items.delete_all.confirm")}
        onCancel={() => setIsConfirmingDeleteAll(false)}
        onConfirm={() => {
          setIsConfirmingDeleteAll(false);
          deleteItem.reset();
          deleteAll.mutate();
        }}
      />
    </>
  );
}
