/**
 * A row of equal choice buttons in a dark pill, such as the Check-ins page's
 * "How often, at most" or the Account page's "How direct Zeph is". The
 * picked one is the cream pill.
 *
 * @param props - `label` names the group for screen readers; `options` are
 *   the choices with their names, in order; `value` is the picked one;
 *   `layoutClassName` sets the group's columns, width and corners;
 *   `disabled` stops changes and `onChange` gets the new choice.
 * @returns The group of choice buttons.
 */
export function ChoiceSegments<Choice extends string>({
  label,
  options,
  value,
  layoutClassName,
  disabled = false,
  onChange,
}: {
  label: string;
  options: { value: Choice; label: string }[];
  value: Choice;
  layoutClassName: string;
  disabled?: boolean;
  onChange: (choice: Choice) => void;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className={`box-border grid w-full gap-1 border border-line bg-bg-deep p-1 ${layoutClassName}`}
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
