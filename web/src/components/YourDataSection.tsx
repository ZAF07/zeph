"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DeletionRow } from "@/components/DeletionRow";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { type Copy, countSlotKey, fillCopy, readCopy } from "@/lib/copy";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Delete my data row: what it removes and how long messages are
 * otherwise kept, with Delete my data behind a confirm dialog. After a
 * delete, every page loads its data again.
 *
 * @param props - `retentionDays` is how many days messages are kept, from
 *   platform settings; `copy` holds the Account page's Copy.
 * @returns The section.
 */
export function YourDataSection({
  retentionDays,
  copy,
}: {
  retentionDays: number;
  copy: Copy;
}) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isConfirming, setIsConfirming] = useState(false);

  const deleteMyData = useMutation({
    mutationFn: () => apiClient.deleteMyData(),
    onSuccess: () => void queryClient.invalidateQueries(),
  });

  return (
    <DeletionRow
      headingId="your-data-heading"
      title={accountCopy("delete_data.heading")}
      description={
        <>
          <p className="mt-1 mb-0 max-w-[620px] text-[14px] text-soft">
            {accountCopy("delete_data.description")}
          </p>
          <p className="mt-1.5 mb-0 text-[13px] text-soft">
            {fillCopy(
              copy,
              countSlotKey("account.delete_data.retention", retentionDays),
              { count: retentionDays },
            )}
          </p>
        </>
      }
      buttonLabel={accountCopy("delete_data.button")}
      deletingLabel={accountCopy("deleting")}
      isDeleting={deleteMyData.isPending}
      onStart={() => {
        deleteMyData.reset();
        setIsConfirming(true);
      }}
    >
      <ConfirmDialog
        open={isConfirming}
        title={accountCopy("delete_data.dialog_title")}
        body={`${accountCopy("delete_data.description")} ${accountCopy("delete_data.dialog_body")}`}
        cancelLabel={accountCopy("delete_data.dialog_cancel")}
        confirmLabel={accountCopy("delete_data.dialog_confirm")}
        onConfirm={() => {
          setIsConfirming(false);
          deleteMyData.mutate();
        }}
        onCancel={() => setIsConfirming(false)}
      />
      {deleteMyData.isSuccess ? (
        <SavedNote>{accountCopy("delete_data.done")}</SavedNote>
      ) : null}
      {deleteMyData.isError ? (
        <SaveFailedNote>{accountCopy("delete_data.failed")}</SaveFailedNote>
      ) : null}
    </DeletionRow>
  );
}
