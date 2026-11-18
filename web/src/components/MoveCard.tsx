"use client";

import { useId, useState } from "react";

import {
  compactSecondaryButton,
  confirmDangerButton,
  secondaryButton,
} from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import {
  ApiError,
  type Feature,
  type FeatureSwitch,
  type MoveDirection,
  type MoveInput,
} from "@/lib/api-client";

/**
 * One Move as an editable card: name, "when it fits", "how to do it", the
 * Feature it needs, whether it asks a question, Move up and down, Save and
 * Remove. A new Move's card has
 * Add and Cancel instead.
 *
 * @param props - `initial` fills the card; `isNew` marks a Move not saved
 *   yet; `features` are the Features it can need; `onSave` saves and
 *   rejects if the backend refuses; `onRemove` removes the Move, or
 *   `onCancel` drops a new one; `onMove` moves it, and `canMoveUp` /
 *   `canMoveDown` say which ways it can go; `isMoving` disables the moves
 *   while one is saving.
 * @returns The card.
 */
export function MoveCard({
  initial,
  isNew,
  features,
  onSave,
  onRemove,
  onCancel,
  onMove,
  canMoveUp = false,
  canMoveDown = false,
  isMoving = false,
}: {
  initial: MoveInput;
  isNew: boolean;
  features: FeatureSwitch[];
  onSave: (move: MoveInput) => Promise<void>;
  onRemove?: () => Promise<void>;
  onCancel?: () => void;
  onMove?: (direction: MoveDirection) => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
  isMoving?: boolean;
}) {
  const fieldId = useId();
  const [name, setName] = useState(initial.name);
  const [whenItFits, setWhenItFits] = useState(initial.when_it_fits);
  const [howToDoIt, setHowToDoIt] = useState(initial.how_to_do_it);
  const [neededFeature, setNeededFeature] = useState<Feature | null>(
    initial.needed_feature,
  );
  const [asksAQuestion, setAsksAQuestion] = useState(initial.asks_a_question);
  const [isBusy, setIsBusy] = useState(false);
  const [isConfirmingRemove, setIsConfirmingRemove] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const title = isNew ? "New Move" : initial.name;
  const isComplete =
    name.trim() !== "" && whenItFits.trim() !== "" && howToDoIt.trim() !== "";
  const isChanged =
    name !== initial.name ||
    whenItFits !== initial.when_it_fits ||
    howToDoIt !== initial.how_to_do_it ||
    neededFeature !== initial.needed_feature ||
    asksAQuestion !== initial.asks_a_question;

  async function run(action: () => Promise<void>, failureText: string) {
    setIsBusy(true);
    setError(null);
    try {
      await action();
    } catch (failure) {
      setError(
        failure instanceof ApiError &&
          (failure.status === 422 || failure.status === 409) &&
          failure.detail
          ? failure.detail
          : failureText,
      );
    } finally {
      setIsBusy(false);
    }
  }

  function save() {
    void run(
      () =>
        onSave({
          name,
          when_it_fits: whenItFits,
          how_to_do_it: howToDoIt,
          needed_feature: neededFeature,
          asks_a_question: asksAQuestion,
        }),
      "Couldn’t save the Move. Please try again.",
    );
  }

  function chooseFeature(value: string) {
    const chosen = features.find((feature) => feature.feature === value);
    setNeededFeature(chosen ? chosen.feature : null);
    setError(null);
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
            placeholder="e.g. Research"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setError(null);
            }}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor={`${fieldId}-when`}>
            When it fits{" "}
            <span className="text-caption font-normal text-ink-muted">
              — Zeph reads this to pick a Move
            </span>
          </label>
          <textarea
            id={`${fieldId}-when`}
            className={`${inputField} resize-y`}
            rows={2}
            value={whenItFits}
            onChange={(event) => {
              setWhenItFits(event.target.value);
              setError(null);
            }}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor={`${fieldId}-how`}>
            How to do it{" "}
            <span className="text-caption font-normal text-ink-muted">
              — goes into the reply when picked
            </span>
          </label>
          <textarea
            id={`${fieldId}-how`}
            className={`${inputField} resize-y`}
            rows={4}
            value={howToDoIt}
            onChange={(event) => {
              setHowToDoIt(event.target.value);
              setError(null);
            }}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor={`${fieldId}-feature`}>
            Needs a Feature{" "}
            <span className="text-caption font-normal text-ink-muted">
              — never offered when it doesn’t work for the User
            </span>
          </label>
          <select
            id={`${fieldId}-feature`}
            className={inputField}
            value={neededFeature ?? ""}
            onChange={(event) => chooseFeature(event.target.value)}
          >
            <option value="">None</option>
            {features.map((feature) => (
              <option key={feature.feature} value={feature.feature}>
                {feature.name}
              </option>
            ))}
          </select>
        </div>
        <label className="flex items-center gap-1.5 text-sm font-medium">
          <input
            type="checkbox"
            checked={asksAQuestion}
            onChange={(event) => {
              setAsksAQuestion(event.target.checked);
              setError(null);
            }}
          />
          Asks a question{" "}
          <span className="text-caption font-normal text-ink-muted">
            — never made twice in a row, or with another question
          </span>
        </label>
      </div>
      {error ? (
        <p
          role="alert"
          className="mx-5 mb-3 rounded-xl border border-danger-line bg-danger-tint px-4 py-3 text-sm text-danger-deep"
        >
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-2.5">
        <span className="flex flex-wrap items-center gap-2">
          {onMove ? (
            <>
              <button
                type="button"
                aria-label={`Move ${initial.name} up`}
                className={compactSecondaryButton}
                disabled={!canMoveUp || isMoving}
                onClick={() => onMove("up")}
              >
                ↑
              </button>
              <button
                type="button"
                aria-label={`Move ${initial.name} down`}
                className={compactSecondaryButton}
                disabled={!canMoveDown || isMoving}
                onClick={() => onMove("down")}
              >
                ↓
              </button>
            </>
          ) : null}
          {isNew ? (
            <span className="text-caption text-ink-muted">Not saved yet</span>
          ) : null}
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
                    "Couldn’t remove the Move. Please try again.",
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
