"use client";

import { useId } from "react";

const boxClass =
  "box-border block w-full rounded-input border border-line-strong bg-bg-deep px-3.5 text-[15px] text-text placeholder:text-mute";

/**
 * A field inside a card: its name, the text box, and an optional hint
 * under it. A long field is a text area that grows with its text.
 *
 * @param props - `label` names it; `hint` says what it is for; `value`,
 *   `placeholder` and `onChange` are the text; `multiline` makes it a text
 *   area.
 * @returns The field.
 */
export function CardTextField({
  label,
  hint,
  value,
  placeholder,
  multiline = false,
  onChange,
}: {
  label: string;
  hint?: string;
  value: string;
  placeholder?: string;
  multiline?: boolean;
  onChange: (value: string) => void;
}) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] text-soft">
        {label}
      </label>
      {multiline ? (
        <textarea
          id={id}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          className={`${boxClass} min-h-24 resize-none py-3 [field-sizing:content]`}
        />
      ) : (
        <input
          id={id}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          className={`${boxClass} min-h-[46px] py-[11px]`}
        />
      )}
      {hint ? <span className="text-[12px] text-soft">{hint}</span> : null}
    </div>
  );
}
