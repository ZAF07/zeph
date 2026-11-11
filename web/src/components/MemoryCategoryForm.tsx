"use client";

import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { fieldLabel, inputField } from "@/components/form-styles";
import { ApiError, type MemoryCategoryInput } from "@/lib/api-client";

/**
 * The form for adding a Memory Category or changing its name and
 * description.
 *
 * @param props - `title` names the form; `initial` fills it; `onSubmit`
 *   saves and rejects if the backend refuses; `onCancel` closes it.
 * @returns The form.
 */
export function MemoryCategoryForm({
  title,
  initial,
  onSubmit,
  onCancel,
}: {
  title: string;
  initial: MemoryCategoryInput;
  onSubmit: (category: MemoryCategoryInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial.name);
  const [description, setDescription] = useState(initial.description);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isComplete = name.trim() !== "" && description.trim() !== "";

  async function submit() {
    setIsSaving(true);
    setError(null);
    try {
      await onSubmit({
        name,
        description,
        always_include: initial.always_include,
      });
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.status === 422 && failure.detail
          ? failure.detail
          : "Couldn’t save the category. Please try again.",
      );
      setIsSaving(false);
    }
  }

  return (
    <form
      aria-label={title}
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-5"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div className="grid gap-3 sm:grid-cols-[1fr_2fr]">
        <div className={fieldLabel}>
          <label htmlFor="memory-category-name">Name</label>
          <input
            id="memory-category-name"
            className={inputField}
            placeholder="e.g. Work"
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setError(null);
            }}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor="memory-category-description">
            Description{" "}
            <span className="text-caption font-normal text-ink-muted">
              — tells Zeph what belongs here
            </span>
          </label>
          <input
            id="memory-category-description"
            className={inputField}
            placeholder="Job, colleagues, career goals"
            value={description}
            onChange={(event) => {
              setDescription(event.target.value);
              setError(null);
            }}
          />
        </div>
      </div>
      {error ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          className={primaryButton}
          disabled={!isComplete || isSaving}
        >
          {isSaving ? "Saving…" : "Save category"}
        </button>
        <button type="button" className={secondaryButton} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
