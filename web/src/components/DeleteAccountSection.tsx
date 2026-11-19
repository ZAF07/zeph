"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DeletionRow } from "@/components/DeletionRow";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { ApiError } from "@/lib/api-client";
import { useSignOut } from "@/lib/auth/client";
import { type Copy, readCopy } from "@/lib/copy";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Delete account row: deletes the User's account and everything of
 * theirs behind a confirm dialog, then signs them out. A refusal the
 * backend explains (such as the last Admin) shows the backend's reason.
 *
 * @param props - `copy` holds the Account page's Copy.
 * @returns The section.
 */
export function DeleteAccountSection({ copy }: { copy: Copy }) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
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
      : accountCopy("delete_account.failed");

  return (
    <DeletionRow
      headingId="delete-account-heading"
      title={accountCopy("delete_account.heading")}
      isDanger
      description={
        <p className="mt-1 mb-0 max-w-[620px] text-[14px] text-soft">
          {accountCopy("delete_account.description")}
        </p>
      }
      buttonLabel={accountCopy("delete_account.button")}
      deletingLabel={accountCopy("deleting")}
      isDeleting={deleteAccount.isPending}
      onStart={() => {
        deleteAccount.reset();
        setIsConfirming(true);
      }}
    >
      <ConfirmDialog
        open={isConfirming}
        title={accountCopy("delete_account.dialog_title")}
        body={accountCopy("delete_account.dialog_body")}
        cancelLabel={accountCopy("delete_account.dialog_cancel")}
        confirmLabel={accountCopy("delete_account.dialog_confirm")}
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
