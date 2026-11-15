"use client";

import { ShapeGroupFields } from "@/components/ShapeGroupFields";
import type { FormShape, FormValues } from "@/lib/api-client";

/**
 * A case or Judge form's sections, each with its heading, what it is for
 * and its fields. The backend's shape draws it, so it shows every field the
 * backend checks, explained.
 *
 * @param props - `shape` describes the form, `value` holds its values,
 *   `errors` are the backend's messages by field path, `disabled` locks it
 *   and `onChange` gets the form's new values.
 * @returns The sections.
 */
export function ShapeFormSections({
  shape,
  value,
  errors,
  disabled,
  onChange,
}: {
  shape: FormShape;
  value: FormValues;
  errors: Record<string, string>;
  disabled: boolean;
  onChange: (value: FormValues) => void;
}) {
  return (
    <>
      {shape.sections.map((section) => (
        <section
          key={section.title}
          aria-label={section.title}
          className="flex flex-col gap-5 rounded-card border border-line bg-white p-6"
        >
          <header className="flex flex-col gap-1">
            <h2 className="m-0 text-h3 font-semibold">{section.title}</h2>
            <p className="m-0 text-caption text-ink-soft">
              {section.description}
            </p>
          </header>
          <ShapeGroupFields
            fields={section.fields}
            value={value}
            path=""
            errors={errors}
            disabled={disabled}
            onChange={onChange}
          />
        </section>
      ))}
    </>
  );
}
