import { EvalImageField } from "@/components/EvalImageField";
import { inputField } from "@/components/form-styles";
import { Switch } from "@/components/Switch";
import type { ShapeFieldProps } from "@/lib/eval-forms";

/**
 * The input for a single-value field, by its kind.
 *
 * @param props - The field's props, plus `inputId` for its label,
 *   `describedBy` for its description and `invalid` when it has an error.
 * @returns The input.
 */
export function ShapeFieldControl({
  field,
  value,
  disabled,
  onChange,
  inputId,
  describedBy,
  invalid,
}: ShapeFieldProps & {
  inputId: string;
  describedBy: string;
  invalid: boolean;
}) {
  const shared = {
    id: inputId,
    disabled,
    "aria-describedby": describedBy,
    "aria-invalid": invalid,
  };
  const text = typeof value === "string" ? value : "";

  if (field.kind === "long_text") {
    return (
      <textarea
        {...shared}
        rows={4}
        className={`${inputField} resize-y`}
        value={text}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }
  if (field.kind === "whole_number") {
    return (
      <input
        {...shared}
        type="number"
        step={1}
        min={field.minimum ?? undefined}
        className={`${inputField} max-w-[180px]`}
        value={typeof value === "number" ? value : ""}
        onChange={(event) =>
          onChange(
            event.target.value === ""
              ? null
              : Math.trunc(Number(event.target.value)),
          )
        }
      />
    );
  }
  if (field.kind === "on_off") {
    return (
      <Switch
        label={field.label}
        checked={value === true}
        disabled={disabled}
        onChange={onChange}
      />
    );
  }
  if (field.kind === "choice") {
    const chosen = field.options.findIndex((option) => option.value === value);
    return (
      <select
        {...shared}
        className={`${inputField} max-w-[320px]`}
        value={chosen === -1 ? "" : String(chosen)}
        onChange={(event) =>
          onChange(
            event.target.value === ""
              ? null
              : field.options[Number(event.target.value)].value,
          )
        }
      >
        <option value="" disabled={field.required}>
          {field.required ? "Pick one" : "Not checked"}
        </option>
        {field.options.map((option, index) => (
          <option key={String(option.value)} value={String(index)}>
            {option.label}
          </option>
        ))}
      </select>
    );
  }
  if (field.kind === "date_time") {
    return (
      <input
        {...shared}
        type="datetime-local"
        className={`${inputField} max-w-[260px]`}
        value={text.slice(0, 16)}
        onChange={(event) =>
          onChange(event.target.value ? `${event.target.value}:00` : null)
        }
      />
    );
  }
  if (field.kind === "image") {
    return (
      <EvalImageField
        inputId={inputId}
        name={text || null}
        disabled={disabled}
        onChange={onChange}
      />
    );
  }
  return (
    <input
      {...shared}
      type="text"
      className={inputField}
      value={text}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
