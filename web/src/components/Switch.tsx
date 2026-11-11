/**
 * An on/off switch, styled like the design's toggles.
 *
 * @param props - `label` names the switch for screen readers, `checked` is
 *   whether it is on, `disabled` stops changes and `onChange` gets the new
 *   value.
 * @returns The switch.
 */
export function Switch({
  label,
  checked,
  disabled = false,
  onChange,
}: {
  label: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`flex h-8 w-[52px] flex-none cursor-pointer rounded-full border-0 p-[3px] disabled:cursor-not-allowed disabled:opacity-60 ${
        checked ? "justify-end bg-blue" : "justify-start bg-line-strong"
      }`}
    >
      <span className="size-[26px] rounded-full bg-white" />
    </button>
  );
}
