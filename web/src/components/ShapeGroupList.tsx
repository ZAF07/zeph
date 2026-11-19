"use client";

import { compactSecondaryButton } from "@/components/button-styles";
import { fieldCaption } from "@/components/form-styles";
import { ShapeGroupFields } from "@/components/ShapeGroupFields";
import {
  emptyGroup,
  fieldPath,
  isFormValues,
  type ShapeFieldProps,
} from "@/lib/eval-forms";

/**
 * A list whose every entry is a group of fields, such as a case's Messages
 * or rules: each entry in its own box, with buttons to add and remove one.
 *
 * @param props - The list field's props; its `value` is the list.
 * @returns The list.
 */
export function ShapeGroupList({
  field,
  value,
  path,
  errors,
  disabled,
  onChange,
}: ShapeFieldProps) {
  const entries = Array.isArray(value) ? value : [];
  const itemLabel = field.item_label || "Entry";
  const error = errors[path];

  function change(index: number, entry: unknown) {
    onChange(entries.map((other, at) => (at === index ? entry : other)));
  }

  return (
    <section aria-label={field.label} className="flex min-w-0 flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <h3 className="m-0 text-[15px] font-normal text-text">{field.label}</h3>
        <p className={fieldCaption}>{field.description}</p>
      </div>
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
              className={compactSecondaryButton}
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
          className={compactSecondaryButton}
          disabled={disabled}
          onClick={() => onChange([...entries, emptyGroup(field.fields)])}
        >
          Add {itemLabel.toLowerCase()}
        </button>
      </div>
    </section>
  );
}
