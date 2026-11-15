"use client";

import { useId } from "react";

import { fieldCaption } from "@/components/form-styles";
import { ShapeFieldControl } from "@/components/ShapeFieldControl";
import { ShapeGroupFields } from "@/components/ShapeGroupFields";
import { ShapeGroupList } from "@/components/ShapeGroupList";
import { ShapeTextList } from "@/components/ShapeTextList";
import { isFormValues, type ShapeFieldProps } from "@/lib/eval-forms";

/**
 * One field of a case or Judge form, drawn from the backend's description
 * of it: its label, what it means and what changing it affects, the input
 * for its kind and the backend's message when a save was refused.
 *
 * @param props - `field` describes it, `value` is its value, `path` is
 *   where it sits (e.g. `messages.0.text`), `errors` are the backend's
 *   messages by path, `disabled` locks it and `onChange` gets a new value.
 * @returns The field.
 */
export function ShapeFieldInput(props: ShapeFieldProps) {
  const { field, value, path, errors, disabled } = props;
  const inputId = useId();
  const descriptionId = `${inputId}-description`;
  const error = errors[path];

  if (field.kind === "group") {
    return (
      <fieldset className="m-0 flex min-w-0 flex-col gap-4 rounded-xl border border-line p-4">
        <legend className="px-1 font-semibold">{field.label}</legend>
        <p className={fieldCaption}>{field.description}</p>
        <ShapeGroupFields
          fields={field.fields}
          value={isFormValues(value) ? value : {}}
          path={path}
          errors={errors}
          disabled={disabled}
          onChange={props.onChange}
        />
      </fieldset>
    );
  }
  if (field.kind === "group_list") {
    return <ShapeGroupList {...props} />;
  }
  if (field.kind === "text_list") {
    return <ShapeTextList {...props} />;
  }

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium">
        {field.label}
        {field.required || field.kind === "on_off" ? null : (
          <span className="font-normal text-ink-muted"> · optional</span>
        )}
      </label>
      <p id={descriptionId} className={fieldCaption}>
        {field.description}
      </p>
      <ShapeFieldControl
        {...props}
        inputId={inputId}
        describedBy={descriptionId}
        invalid={error !== undefined}
      />
      {error ? (
        <p role="alert" className="m-0 text-caption text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
