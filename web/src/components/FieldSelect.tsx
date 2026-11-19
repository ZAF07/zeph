import { fieldBox } from "@/components/field-styles";

/**
 * A choice in a field row, drawn as the value box with a down chevron.
 *
 * @param props - `id` ties it to the row's name; `value` is the chosen
 *   option's value; `options` are the choices, each a value and the label
 *   shown for it; `onChange` gets the new choice's value.
 * @returns The select.
 */
export function FieldSelect({
  id,
  value,
  options,
  onChange,
}: {
  id: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <span className={`${fieldBox} relative px-0`}>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full min-w-0 cursor-pointer appearance-none border-0 bg-transparent pr-9 pl-3.5 text-[15px] text-text"
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            className="bg-bg-deep"
          >
            {option.label}
          </option>
        ))}
      </select>
      <svg
        aria-hidden="true"
        width="12"
        height="8"
        viewBox="0 0 12 8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        className="pointer-events-none absolute right-3.5 text-soft"
      >
        <path d="M1 1.5l5 5 5-5" />
      </svg>
    </span>
  );
}
