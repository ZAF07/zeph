"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { dangerButton } from "@/components/button-styles";
import { DeleteConfirmation } from "@/components/DeleteConfirmation";
import { ApiError } from "@/lib/api-client";
import { useSignOut } from "@/lib/auth/client";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Delete account section: deletes the User's account and everything of
 * theirs behind a type-DELETE confirmation, then signs them out.
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
    onError: () => setIsConfirming(false),
  });
  const { error } = deleteAccount;
  const failureMessage =
    error instanceof ApiError && error.status === 409 && error.detail
      ? error.detail
      : "We couldn’t delete your account. Please try again.";

  return (
    <section
      aria-labelledby="delete-account-heading"
      className="flex flex-col gap-3 rounded-card border border-danger-line p-6"
    >
      <h2
        id="delete-account-heading"
        className="m-0 text-[17px] font-semibold text-danger"
      >
        Delete account
      </h2>
      <p className="m-0 text-[15px] text-ink-soft">
        Erases everything above plus your account. Only possible here on the
        Dashboard. This can’t be undone.
      </p>
      {isConfirming ? (
        <DeleteConfirmation
          confirmLabel="Permanently delete account"
          cancelLabel="Keep my account"
          isDeleting={deleteAccount.isPending}
          onConfirm={() => deleteAccount.mutate()}
          onCancel={() => setIsConfirming(false)}
        />
      ) : (
        <button
          type="button"
          className={`${dangerButton} self-start`}
          onClick={() => {
            deleteAccount.reset();
            setIsConfirming(true);
          }}
        >
          Delete my account
        </button>
      )}
      {deleteAccount.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          {failureMessage}
        </p>
      ) : null}
    </section>
  );
}
