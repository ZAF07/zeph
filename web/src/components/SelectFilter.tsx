/** One choice in a select filter. */
export type SelectFilterOption = { value: string; label: string };

/**
 * A drop-down filter above an admin table, such as the period, drawn as a
 * box with the choice and a chevron. The native select lies unseen over the
 * box, so it is as wide as the choice shown, not the longest one.
 *
 * @param props - `label` names it for screen readers, `options` are the
 *   choices, `value` is the current one and `onChange` gets a new one.
 * @returns The select.
 */
export function SelectFilter({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: SelectFilterOption[];
  value: string;
  onChange: (value: string) => void;
}) {
  const chosen = options.find((option) => option.value === value);
  return (
    <div className="relative inline-flex rounded-input has-[select:focus-visible]:outline-2 has-[select:focus-visible]:outline-offset-2 has-[select:focus-visible]:outline-cream has-[select:focus-visible]:outline-solid">
      <span
        aria-hidden="true"
        className="box-border inline-flex min-h-11 items-center gap-2.5 rounded-input border border-line-strong bg-panel px-[14px] text-[14px] text-text"
      >
        {chosen?.label}
        <svg
          width="12"
          height="8"
          viewBox="0 0 12 8"
          fill="none"
          stroke="var(--color-soft)"
          strokeWidth="1.5"
          strokeLinecap="round"
        >
          <path d="M1 1.5l5 5 5-5" />
        </svg>
      </span>
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="absolute inset-0 cursor-pointer appearance-none opacity-0"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
