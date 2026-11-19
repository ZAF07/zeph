import { fieldBox } from "@/components/field-styles";

/**
 * A short line of text in a field row, drawn as the value box.
 *
 * @param props - `id` ties it to the row's name; `value` is the text;
 *   `placeholder` is the grey hint shown while it is empty; `onChange` gets
 *   the new text.
 * @returns The text box.
 */
export function FieldText({
  id,
  value,
  placeholder,
  onChange,
}: {
  id: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <span className={fieldBox}>
      <input
        id={id}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full min-w-0 border-0 bg-transparent p-0 text-[15px] text-text placeholder:text-mute"
      />
    </span>
  );
}
