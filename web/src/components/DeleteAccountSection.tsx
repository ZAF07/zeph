"use client";

import { useState } from "react";

import { dangerButton } from "@/components/button-styles";
import { DeleteConfirmation } from "@/components/DeleteConfirmation";
import { ApiError } from "@/lib/api-client";
import { useSignOut } from "@/lib/auth/client";
import { useApiClient } from "@/lib/use-api-client";

type DeleteState =
  | { kind: "idle" }
  | { kind: "confirming" }
  | { kind: "deleting" }
  | { kind: "failed"; message: string };

/**
 * The Delete account section: deletes the User's account and everything of
 * theirs behind a type-DELETE confirmation, then signs them out.
 *
 * @returns The section.
 */
export function DeleteAccountSection() {
  const apiClient = useApiClient();
  const signOut = useSignOut();
  const [deleteState, setDeleteState] = useState<DeleteState>({
    kind: "idle",
  });
  const isConfirming =
    deleteState.kind === "confirming" || deleteState.kind === "deleting";

  async function deleteAccount() {
    setDeleteState({ kind: "deleting" });
    try {
      await apiClient.deleteAccount();
    } catch (error) {
      setDeleteState({
        kind: "failed",
        message:
          error instanceof ApiError && error.status === 409 && error.detail
            ? error.detail
            : "We couldn’t delete your account. Please try again.",
      });
      return;
    }
    await signOut("/sign-in");
  }

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
          isDeleting={deleteState.kind === "deleting"}
          onConfirm={() => void deleteAccount()}
          onCancel={() => setDeleteState({ kind: "idle" })}
        />
      ) : (
        <button
          type="button"
          className={`${dangerButton} self-start`}
          onClick={() => setDeleteState({ kind: "confirming" })}
        >
          Delete my account
        </button>
      )}
      {deleteState.kind === "failed" ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          {deleteState.message}
        </p>
      ) : null}
    </section>
  );
}
