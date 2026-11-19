import { filterPillClass } from "@/components/filter-pill-styles";

/**
 * A filter above an admin table that is on or off, such as "Errors only",
 * drawn as one filter pill: cream while on.
 *
 * @param props - `label` is the pill's text, `on` says whether it is on,
 *   and `onChange` gets the new value.
 * @returns The toggle.
 */
export function FilterToggle({
  label,
  on,
  onChange,
}: {
  label: string;
  on: boolean;
  onChange: (on: boolean) => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={() => onChange(!on)}
      className={filterPillClass(on)}
    >
      {label}
    </button>
  );
}
