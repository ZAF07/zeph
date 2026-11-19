import type { CheckInFrequency } from "@/lib/api-client";

/**
 * The Check-ins page's "How often, at most" choice: one row of four equal
 * segments from 900px up, two rows of two on a phone. The picked one is the
 * cream pill.
 *
 * @param props - `label` names the group for screen readers; `options` are
 *   the frequencies with their names, in order; `value` is the picked
 *   frequency, `disabled` stops changes and `onChange` gets the new one.
 * @returns The group of choice buttons.
 */
export function CheckInFrequencySegments({
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
      className="box-border grid w-full grid-cols-2 gap-1 rounded-[28px] border border-line bg-bg-deep p-1 min-[900px]:mx-auto min-[900px]:max-w-[640px] min-[900px]:grid-cols-4 min-[900px]:rounded-pill"
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
            className={`min-h-12 cursor-pointer rounded-pill border-0 px-2 py-1 text-center text-[13px] leading-[1.2] disabled:cursor-not-allowed ${
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
