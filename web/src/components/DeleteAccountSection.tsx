"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DeletionRow } from "@/components/DeletionRow";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { ApiError } from "@/lib/api-client";
import { useSignOut } from "@/lib/auth/client";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Delete account row: deletes the User's account and everything of
 * theirs behind a confirm dialog, then signs them out.
 *
 * @returns The section.
 */
export function DeleteAccountSection() {
  const apiClient = useApiClient();
  const signOut = useSignOut();
  const [isConfirming, setIsConfirming] = useState(false);

  const deleteAccount = useMutation({
    mutationFn: () => apiClient.deleteAccount(),
    onSuccess: () => signOut("/sign-in"),
  });
  const { error } = deleteAccount;
  const failureMessage =
    error instanceof ApiError && error.status === 409 && error.detail
      ? error.detail
      : "We couldn’t delete your account. Please try again.";

  return (
    <DeletionRow
      headingId="delete-account-heading"
      title="Delete account"
      isDanger
      description={
        <p className="mt-1 mb-0 max-w-[620px] text-[14px] text-soft">
          Erases everything above plus your account. Only possible here on the
          Dashboard. This can’t be undone.
        </p>
      }
      buttonLabel="Delete my account"
      isDeleting={deleteAccount.isPending}
      onStart={() => {
        deleteAccount.reset();
        setIsConfirming(true);
      }}
    >
      <ConfirmDialog
        open={isConfirming}
        title="Delete your account?"
        body="Erases everything above plus your account. This can’t be undone."
        cancelLabel="Keep my account"
        confirmLabel="Permanently delete account"
        onConfirm={() => {
          setIsConfirming(false);
          deleteAccount.mutate();
        }}
        onCancel={() => setIsConfirming(false)}
      />
      {deleteAccount.isError ? (
        <SaveFailedNote>{failureMessage}</SaveFailedNote>
      ) : null}
    </DeletionRow>
  );
}
