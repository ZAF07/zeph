/**
 * An on/off switch, styled like the design's toggles.
 *
 * @param props - `label` names the switch for screen readers, `checked` is
 *   whether it is on, `disabled` stops changes, `describedById` is the id
 *   of a note about the switch, if any, and `onChange` gets the new value.
 * @returns The switch.
 */
export function Switch({
  label,
  checked,
  disabled = false,
  describedById,
  onChange,
}: {
  label: string;
  checked: boolean;
  disabled?: boolean;
  describedById?: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      aria-describedby={describedById}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="relative size-11 flex-none cursor-pointer border-0 bg-transparent p-0 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <span
        className={`absolute left-[2px] top-[11px] h-[22px] w-10 rounded-[11px] ${
          checked ? "bg-cream" : "bg-line"
        }`}
      />
      <span
        className={`absolute top-[14px] size-4 rounded-full ${
          checked ? "left-[23px] bg-ink" : "left-[5px] bg-soft"
        }`}
      />
    </button>
  );
}
