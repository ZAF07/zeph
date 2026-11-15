"use client";

import { ShapeFieldInput } from "@/components/ShapeFieldInput";
import type { FormValues, ShapeField } from "@/lib/api-client";
import { fieldPath } from "@/lib/eval-forms";

/**
 * The fields of one group, such as a Life Thread or a form section, each
 * changing its own value inside the group.
 *
 * @param props - `fields` describe them, `value` holds their values by
 *   name, `path` is the group's path ("" at the top), `errors` are the
 *   backend's messages by path, `disabled` locks them and `onChange` gets
 *   the group's new value.
 * @returns The fields.
 */
export function ShapeGroupFields({
  fields,
  value,
  path,
  errors,
  disabled,
  onChange,
}: {
  fields: ShapeField[];
  value: FormValues;
  path: string;
  errors: Record<string, string>;
  disabled: boolean;
  onChange: (value: FormValues) => void;
}) {
  return (
    <div className="flex flex-col gap-5">
      {fields.map((field) => (
        <ShapeFieldInput
          key={field.name}
          field={field}
          value={value[field.name]}
          path={fieldPath(path, field.name)}
          errors={errors}
          disabled={disabled}
          onChange={(fieldValue) =>
            onChange({ ...value, [field.name]: fieldValue })
          }
        />
      ))}
    </div>
  );
}
