"use client";

import { SectionFields } from "@/components/SectionFields";
import type { FormShape, FormValues } from "@/lib/api-client";

/**
 * A case or Judge form's sections, each a panel with its heading, its hint
 * and its fields. The backend's shape draws it, so it shows every field the
 * backend checks. A section that is one list draws the list's entries
 * straight in the panel, as the Day Summary case's "The day" does.
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
          className="box-border flex flex-col gap-[14px] rounded-card border border-line bg-panel px-6 py-[22px]"
        >
          <div>
            <h2 className="m-0 text-[17px] font-normal text-cream">
              {section.title}
            </h2>
            <p className="mt-1 mb-0 max-w-[640px] text-[13px] text-soft">
              {section.description}
            </p>
          </div>
          <SectionFields
            section={section}
            value={value}
            errors={errors}
            disabled={disabled}
            onChange={onChange}
          />
        </section>
      ))}
    </>
  );
}
