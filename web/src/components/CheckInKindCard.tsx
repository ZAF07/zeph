"use client";

import { useId, useState } from "react";

import {
  compactSecondaryButton,
  confirmDangerButton,
  secondaryButton,
} from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { ApiError, type CheckInKindInput } from "@/lib/api-client";

/**
 * One Check-in Kind as an editable card: name, description, how often it
 * was sent, Save and Remove. A new Kind's card has Add and Cancel instead.
 * A Kind that sends a Shared Photo says so, and who it goes to.
 *
 * @param props - `initial` fills the card; `isNew` marks a Kind not saved
 *   yet; `sentLast30Days` is the send count; `sendsSharedPhoto` marks a
 *   Kind that sends a Shared Photo; `onSave` saves and rejects if the
 *   backend refuses; `onRemove` removes the Kind, or `onCancel` drops a new
 *   one.
 * @returns The card.
 */
export function CheckInKindCard({
  initial,
  isNew,
  sentLast30Days,
  sendsSharedPhoto = false,
  onSave,
  onRemove,
  onCancel,
}: {
  initial: CheckInKindInput;
  isNew: boolean;
  sentLast30Days: number;
  sendsSharedPhoto?: boolean;
  onSave: (kind: CheckInKindInput) => Promise<void>;
  onRemove?: () => Promise<void>;
  onCancel?: () => void;
}) {
  const fieldId = useId();
  const [name, setName] = useState(initial.name);
  const [description, setDescription] = useState(initial.description);
  const [isBusy, setIsBusy] = useState(false);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const title = isNew ? "New Check-in Kind" : initial.name;
  const isComplete = name.trim() !== "" && description.trim() !== "";
  const isChanged =
    name !== initial.name || description !== initial.description;

  async function run(action: () => Promise<void>, failureText: string) {
    setIsBusy(true);
    setError(null);
    try {
      await action();
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.status === 422 && failure.detail
          ? failure.detail
          : failureText,
      );
    } finally {
      setIsBusy(false);
    }
  }

  function save() {
    void run(
      () => onSave({ name, description }),
      "Couldn’t save the Check-in Kind. Please try again.",
    );
  }

  return (
    <section
      aria-label={title}
      className="flex flex-col rounded-card border border-line bg-white"
    >
      <div className="flex flex-col gap-3 px-5 pt-[18px] pb-3">
        <div className={fieldLabel}>
          <label htmlFor={`${fieldId}-name`}>Name</label>
          <input
            id={`${fieldId}-name`}
            className={inputField}
            placeholder="e.g. A casual hello"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setError(null);
            }}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor={`${fieldId}-description`}>
            Description{" "}
            <span className="text-caption font-normal text-ink-muted">
              — Zeph uses this to choose
            </span>
          </label>
          <textarea
            id={`${fieldId}-description`}
            className={`${inputField} resize-y`}
            rows={3}
            value={description}
            onChange={(event) => {
              setDescription(event.target.value);
              setError(null);
            }}
          />
        </div>
      </div>
      {sendsSharedPhoto ? (
        <div className="flex min-w-0 flex-col border-t border-line px-5 py-3">
          <span className="font-medium">Sends a Shared Photo</span>
          <span className="text-caption text-ink-muted">
            Only for Users with Photo Viewing on and a Shared Photo
          </span>
        </div>
      ) : null}
      {error ? (
        <p
          role="alert"
          className="mx-5 mb-3 rounded-xl border border-danger-line bg-danger-tint px-4 py-3 text-sm text-danger-deep"
        >
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-2.5">
        <span className="text-caption text-ink-muted">
          {isNew
            ? "Not saved yet"
            : `Sent ${sentLast30Days} ${sentLast30Days === 1 ? "time" : "times"} in 30 days`}
        </span>
        <span className="flex flex-wrap gap-2">
          {isConfirmingRemove && onRemove ? (
            <>
              <button
                type="button"
                className={`${confirmDangerButton} min-h-10 px-3.5 py-2 text-sm`}
                disabled={isBusy}
                onClick={() =>
                  void run(
                    onRemove,
                    "Couldn’t remove the Check-in Kind. Please try again.",
                  )
                }
              >
                Remove {initial.name}
              </button>
              <button
                type="button"
                className={compactSecondaryButton}
                disabled={isBusy}
                onClick={() => setIsConfirmingRemove(false)}
              >
                Keep
              </button>
            </>
          ) : (
            <>
              {onRemove ? (
                <button
                  type="button"
                  className={compactSecondaryButton}
                  disabled={isBusy}
                  onClick={() => setIsConfirmingRemove(true)}
                >
                  Remove
                </button>
              ) : null}
              {onCancel ? (
                <button
                  type="button"
                  className={compactSecondaryButton}
                  disabled={isBusy}
                  onClick={onCancel}
                >
                  Cancel
                </button>
              ) : null}
              <button
                type="button"
                className={`${secondaryButton} min-h-10 py-2`}
                disabled={!isComplete || (!isNew && !isChanged) || isBusy}
                onClick={save}
              >
                {isNew ? "Add" : "Save"}
              </button>
            </>
          )}
        </span>
      </div>
    </section>
  );
}
