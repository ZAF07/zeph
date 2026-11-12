"use client";

import { useState } from "react";

import { dangerButton } from "@/components/button-styles";
import { DeleteConfirmation } from "@/components/DeleteConfirmation";
import { useApiClient } from "@/lib/use-api-client";

type DeleteState = "idle" | "confirming" | "deleting" | "deleted" | "failed";

/**
 * The Your data section: how long messages are kept, and Delete my data
 * behind a type-DELETE confirmation.
 *
 * @param props - `retentionDays` is how many days messages are kept, from
 *   platform settings.
 * @returns The section.
 */
export function YourDataSection({ retentionDays }: { retentionDays: number }) {
  const apiClient = useApiClient();
  const [deleteState, setDeleteState] = useState<DeleteState>("idle");
  const isConfirming =
    deleteState === "confirming" || deleteState === "deleting";

  async function deleteMyData() {
    setDeleteState("deleting");
    try {
      await apiClient.deleteMyData();
      setDeleteState("deleted");
    } catch {
      setDeleteState("failed");
    }
  }

  return (
    <section
      aria-labelledby="your-data-heading"
      className="flex flex-col rounded-card border border-line bg-white"
    >
      <h2
        id="your-data-heading"
        className="m-0 px-6 pb-2 pt-5 text-[17px] font-semibold"
      >
        Your data
      </h2>
      <p className="m-0 px-6 pb-4 text-[15px] text-ink-soft">
        Messages are deleted automatically after {retentionDays}{" "}
        {retentionDays === 1 ? "day" : "days"}. Summaries and memories stay
        until you delete them.
      </p>
      <div className="flex flex-wrap items-start justify-between gap-4 border-t border-line px-6 py-4">
        <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-0.5">
          <span className="font-semibold">Delete my data</span>
          <span className="text-caption text-ink-muted">
            Removes your messages, memories, Conversation Summaries, Check-in
            history and Telegram Connection. Your account stays, so you can
            start fresh.
          </span>
          <span className="text-caption text-blue">
            You can also tell Zeph “delete my data” — it will ask for the
            confirmation word.
          </span>
        </span>
        {isConfirming ? null : (
          <button
            type="button"
            className={dangerButton}
            onClick={() => setDeleteState("confirming")}
          >
            Delete my data
          </button>
        )}
      </div>
      {isConfirming ? (
        <div className="mx-6 mb-5">
          <DeleteConfirmation
            confirmLabel="Delete my data"
            cancelLabel="Cancel"
            isDeleting={deleteState === "deleting"}
            onConfirm={() => void deleteMyData()}
            onCancel={() => setDeleteState("idle")}
          />
        </div>
      ) : null}
      {deleteState === "deleted" ? (
        <p role="status" className="m-0 px-6 pb-5 text-sm text-blue-deep">
          Your data has been deleted. Connect Telegram again whenever you want
          to start fresh.
        </p>
      ) : null}
      {deleteState === "failed" ? (
        <p role="alert" className="m-0 px-6 pb-5 text-sm text-danger-deep">
          We couldn’t delete your data. Please try again.
        </p>
      ) : null}
    </section>
  );
}
