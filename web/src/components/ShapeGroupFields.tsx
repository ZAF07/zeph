"use client";

import { ShapeFieldInput } from "@/components/ShapeFieldInput";
import type { FormValues, ShapeField } from "@/lib/api-client";
import { fieldPath, isShortField } from "@/lib/eval-forms";

/**
 * The fields of one group, such as a Life Thread or a form section, each
 * changing its own value inside the group. Short fields, such as a
 * message's From and Time, sit side by side; the rest take a whole row.
 *
 * @param props - `fields` describe them, `value` holds their values by
 *   name, `path` is the group's path ("" at the top), `errors` are the
 *   backend's messages by path, `disabled` locks them, `inEntry` is true
 *   inside a list entry and `onChange` gets the group's new value.
 * @returns The fields.
 */
export function ShapeGroupFields({
  fields,
  value,
  path,
  errors,
  disabled,
  inEntry = false,
  onChange,
}: {
  fields: ShapeField[];
  value: FormValues;
  path: string;
  errors: Record<string, string>;
  disabled: boolean;
  inEntry?: boolean;
  onChange: (value: FormValues) => void;
}) {
  return (
    <div className="flex flex-wrap gap-[14px]">
      {fields.map((field) => (
        <div
          key={field.name}
          className={
            isShortField(field)
              ? "flex min-w-0 flex-[1_1_160px] flex-col"
              : "flex min-w-0 flex-[1_1_100%] flex-col"
          }
        >
          <ShapeFieldInput
            field={field}
            value={value[field.name]}
            path={fieldPath(path, field.name)}
            errors={errors}
            disabled={disabled}
            inEntry={inEntry}
            onChange={(fieldValue) =>
              onChange({ ...value, [field.name]: fieldValue })
            }
          />
        </div>
      ))}
    </div>
  );
}
