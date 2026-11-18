"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DeletionRow } from "@/components/DeletionRow";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Delete my data row: what it removes and how long messages are
 * otherwise kept, with Delete my data behind a confirm dialog. After a
 * delete, every page loads its data again.
 *
 * @param props - `retentionDays` is how many days messages are kept and
 *   `deleteMyDataDescription` says what Delete my data removes, both from
 *   platform settings.
 * @returns The section.
 */
export function YourDataSection({
  retentionDays,
  deleteMyDataDescription,
}: {
  retentionDays: number;
  deleteMyDataDescription: string;
}) {
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
      title="Delete my data"
      description={
        <>
          <p className="mt-1 mb-0 max-w-[620px] text-[14px] text-soft">
            {deleteMyDataDescription}
          </p>
          <p className="mt-1.5 mb-0 text-[13px] text-soft">
            Messages are otherwise kept for {retentionDays}{" "}
            {retentionDays === 1 ? "day" : "days"}.
          </p>
        </>
      }
      buttonLabel="Delete my data"
      isDeleting={deleteMyData.isPending}
      onStart={() => {
        deleteMyData.reset();
        setIsConfirming(true);
      }}
    >
      <ConfirmDialog
        open={isConfirming}
        title="Delete my data?"
        body={`${deleteMyDataDescription} This can’t be undone.`}
        cancelLabel="Keep my data"
        confirmLabel="Delete my data"
        onConfirm={() => {
          setIsConfirming(false);
          deleteMyData.mutate();
        }}
        onCancel={() => setIsConfirming(false)}
      />
      {deleteMyData.isSuccess ? (
        <SavedNote>
          Your data has been deleted. Connect Telegram again whenever you want
          to start fresh.
        </SavedNote>
      ) : null}
      {deleteMyData.isError ? (
        <SaveFailedNote>
          We couldn’t delete your data. Please try again.
        </SaveFailedNote>
      ) : null}
    </DeletionRow>
  );
}
