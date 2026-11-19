import { fieldBox } from "@/components/field-styles";

/**
 * A whole-number setting in a field row, drawn as the value box with its
 * unit at the end.
 *
 * @param props - `id` ties it to the row's name; `value` is the typed
 *   text; `unit` says what the number counts; `describedById` is the id of a
 *   note about it; `onChange` gets the new text.
 * @returns The number box.
 */
export function FieldNumber({
  id,
  value,
  unit,
  describedById,
  onChange,
}: {
  id: string;
  value: string;
  unit: string;
  describedById?: string;
  onChange: (value: string) => void;
}) {
  return (
    <span className={fieldBox}>
      <input
        id={id}
        type="number"
        inputMode="numeric"
        aria-describedby={describedById}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full min-w-0 border-0 bg-transparent p-0 text-[15px] text-text"
      />
      <span className="flex-none text-[13px] text-soft">{unit}</span>
    </span>
  );
}
