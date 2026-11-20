"use client";

import { ShapeGroupFields } from "@/components/ShapeGroupFields";
import { ShapeGroupList } from "@/components/ShapeGroupList";
import type { FormValues, ShapeSection } from "@/lib/api-client";

/**
 * The fields of one form section. A section that is one list draws the
 * list's entries straight in the panel, its heading standing for the list.
 *
 * @param props - `section` describes it, `value` holds the form's values,
 *   `errors` are the backend's messages by field path, `disabled` locks it
 *   and `onChange` gets the form's new values.
 * @returns The fields.
 */
export function SectionFields({
  section,
  value,
  errors,
  disabled,
  onChange,
}: {
  section: ShapeSection;
  value: FormValues;
  errors: Record<string, string>;
  disabled: boolean;
  onChange: (value: FormValues) => void;
}) {
  const [onlyField] = section.fields;
  if (section.fields.length === 1 && onlyField.kind === "group_list") {
    return (
      <ShapeGroupList
        field={onlyField}
        value={value[onlyField.name]}
        path={onlyField.name}
        errors={errors}
        disabled={disabled}
        bare
        onChange={(listValue) =>
          onChange({ ...value, [onlyField.name]: listValue })
        }
      />
    );
  }
  return (
    <ShapeGroupFields
      fields={section.fields}
      value={value}
      path=""
      errors={errors}
      disabled={disabled}
      onChange={onChange}
    />
  );
}
