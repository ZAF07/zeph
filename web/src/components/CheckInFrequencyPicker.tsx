import type { CheckInFrequency } from "@/lib/api-client";
import { checkInFrequencyOptions } from "@/lib/check-ins";

/**
 * The "How often, at most" choice between once a week, a few times a week
 * and most days.
 *
 * @param props - `value` is the picked frequency, `disabled` stops changes
 *   and `onChange` gets the new one.
 * @returns The group of choice buttons.
 */
export function CheckInFrequencyPicker({
  value,
  disabled = false,
  onChange,
}: {
  value: CheckInFrequency;
  disabled?: boolean;
  onChange: (frequency: CheckInFrequency) => void;
}) {
  return (
    <div
      role="group"
      aria-label="How often"
      className="inline-flex flex-wrap gap-1 self-start rounded-3xl bg-code p-1"
    >
      {checkInFrequencyOptions.map((option) => {
        const isPicked = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isPicked}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={`min-h-10 cursor-pointer rounded-full border-0 px-[18px] py-2.5 text-sm font-medium disabled:cursor-not-allowed ${
              isPicked
                ? "bg-white text-ink shadow-[0_1px_3px_rgba(0,0,0,0.12)]"
                : "bg-transparent text-ink-soft"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
