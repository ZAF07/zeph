"use client";

import { entryButton } from "@/components/button-styles";
import { fieldHint } from "@/components/form-styles";
import { ShapeGroupFields } from "@/components/ShapeGroupFields";
import {
  addEntryLabel,
  emptyGroup,
  fieldPath,
  isFormValues,
  type ShapeFieldProps,
} from "@/lib/eval-forms";

/**
 * A list whose every entry is a group of fields, such as a case's Messages
 * or rules: each entry in its own inset box with its Remove button, and an
 * Add button under the last one. When the list is its section's only field,
 * the section's heading stands for it and the list draws no heading.
 *
 * @param props - The list field's props, its `value` being the list, plus
 *   `bare` to leave out the list's own heading.
 * @returns The list.
 */
export function ShapeGroupList({
  field,
  value,
  path,
  errors,
  disabled,
  onChange,
  bare = false,
}: ShapeFieldProps & { bare?: boolean }) {
  const entries = Array.isArray(value) ? value : [];
  const itemLabel = field.item_label || "Entry";
  const error = errors[path];

  function change(index: number, entry: unknown) {
    onChange(entries.map((other, at) => (at === index ? entry : other)));
  }

  return (
    <section
      aria-label={field.label}
      className="flex min-w-0 flex-col gap-[14px]"
    >
      {bare ? null : (
        <div className="flex flex-col gap-1">
          <h3 className="m-0 text-[13px] font-normal text-soft">
            {field.label}
          </h3>
          {field.description ? (
            <p className={fieldHint}>{field.description}</p>
          ) : null}
        </div>
      )}
      {entries.map((entry, index) => (
        <div
          key={index}
          role="group"
          aria-label={`${itemLabel} ${index + 1}`}
          className="flex flex-col gap-4 rounded-tile border border-line bg-bg-deep p-4"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[14px] text-soft">
              {itemLabel} {index + 1}
            </span>
            <button
              type="button"
              className={entryButton}
              disabled={disabled}
              onClick={() =>
                onChange(entries.filter((_other, at) => at !== index))
              }
            >
              Remove {itemLabel.toLowerCase()} {index + 1}
            </button>
          </div>
          {errors[fieldPath(path, index)] ? (
            <p role="alert" className="m-0 text-[13px] text-danger">
              {errors[fieldPath(path, index)]}
            </p>
          ) : null}
          <ShapeGroupFields
            fields={field.fields}
            value={isFormValues(entry) ? entry : {}}
            path={fieldPath(path, index)}
            errors={errors}
            disabled={disabled}
            inEntry
            onChange={(next) => change(index, next)}
          />
        </div>
      ))}
      {error ? (
        <p role="alert" className="m-0 text-[13px] text-danger">
          {error}
        </p>
      ) : null}
      <div>
        <button
          type="button"
          className={entryButton}
          disabled={disabled}
          onClick={() => onChange([...entries, emptyGroup(field.fields)])}
        >
          {addEntryLabel(itemLabel)}
        </button>
      </div>
    </section>
  );
}
