"use client";

import { compactSecondaryButton } from "@/components/button-styles";
import { fieldCaption, inputField } from "@/components/form-styles";
import { fieldPath, type ShapeFieldProps } from "@/lib/eval-forms";

/**
 * A list of short texts, such as a Message's expected Needs: one line per
 * entry, with buttons to add and remove one.
 *
 * @param props - The list field's props; its `value` is the list of texts.
 * @returns The list.
 */
export function ShapeTextList({
  field,
  value,
  path,
  errors,
  disabled,
  onChange,
}: ShapeFieldProps) {
  const entries = Array.isArray(value)
    ? value.map((entry) => (typeof entry === "string" ? entry : ""))
    : [];
  const itemLabel = field.item_label || "Entry";
  const error = errors[path];

  return (
    <section aria-label={field.label} className="flex min-w-0 flex-col gap-2">
      <div className="flex flex-col gap-1.5">
        <h3 className="m-0 text-sm font-medium">
          {field.label}
          {field.required ? null : (
            <span className="font-normal text-ink-muted"> · optional</span>
          )}
        </h3>
        <p className={fieldCaption}>{field.description}</p>
      </div>
      {entries.map((entry, index) => (
        <div key={index} className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <input
              type="text"
              aria-label={`${itemLabel} ${index + 1}`}
              className={inputField}
              value={entry}
              disabled={disabled}
              onChange={(event) =>
                onChange(
                  entries.map((other, at) =>
                    at === index ? event.target.value : other,
                  ),
                )
              }
            />
            <button
              type="button"
              className={compactSecondaryButton}
              disabled={disabled}
              aria-label={`Remove ${itemLabel.toLowerCase()} ${index + 1}`}
              onClick={() =>
                onChange(entries.filter((_other, at) => at !== index))
              }
            >
              Remove
            </button>
          </div>
          {errors[fieldPath(path, index)] ? (
            <p role="alert" className="m-0 text-caption text-danger">
              {errors[fieldPath(path, index)]}
            </p>
          ) : null}
        </div>
      ))}
      {error ? (
        <p role="alert" className="m-0 text-caption text-danger">
          {error}
        </p>
      ) : null}
      <div>
        <button
          type="button"
          className={compactSecondaryButton}
          disabled={disabled}
          onClick={() => onChange([...entries, ""])}
        >
          Add {itemLabel.toLowerCase()}
        </button>
      </div>
    </section>
  );
}
