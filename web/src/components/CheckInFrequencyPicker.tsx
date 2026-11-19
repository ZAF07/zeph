import type { CheckInFrequency } from "@/lib/api-client";

/**
 * The "How often, at most" choice between weekly, a few times a week,
 * most days and a few times a day.
 *
 * @param props - `label` names the group for screen readers; `options` are
 *   the frequencies in order, each with its words; `value` is the picked
 *   frequency, `disabled` stops changes and `onChange` gets the new one.
 * @returns The group of choice buttons.
 */
export function CheckInFrequencyPicker({
  label,
  options,
  value,
  disabled = false,
  onChange,
}: {
  label: string;
  options: { value: CheckInFrequency; label: string }[];
  value: CheckInFrequency;
  disabled?: boolean;
  onChange: (frequency: CheckInFrequency) => void;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className="box-border flex flex-wrap rounded-pill border border-line bg-bg-deep p-1"
    >
      {options.map((option) => {
        const isPicked = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isPicked}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={`min-h-11 flex-[1_1_auto] cursor-pointer rounded-pill border-0 px-3 text-[13px] disabled:cursor-not-allowed ${
              isPicked
                ? "bg-cream font-medium text-ink"
                : "bg-transparent font-light text-soft"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
