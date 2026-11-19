import { filterPillClass } from "@/components/filter-pill-styles";

/** One choice in a row of filter pills. */
export type FilterPillOption<Choice extends string> = {
  id: Choice;
  label: string;
};

/**
 * A row of pill buttons above an admin table, of which one is chosen. The
 * chosen pill is cream.
 *
 * @param props - `label` names the group, `options` are the choices,
 *   `chosen` is the current one and `onChoose` gets a new one.
 * @returns The pills.
 */
export function FilterPills<Choice extends string>({
  label,
  options,
  chosen,
  onChoose,
}: {
  label: string;
  options: FilterPillOption<Choice>[];
  chosen: Choice;
  onChoose: (choice: Choice) => void;
}) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-1.5">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          aria-pressed={chosen === option.id}
          onClick={() => onChoose(option.id)}
          className={filterPillClass(chosen === option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
