/** The search box's look, as the admin table pages draw it. */
const searchInput =
  "box-border min-h-11 w-full rounded-input border border-line-strong bg-panel px-[14px] font-[inherit] text-[14px] text-text placeholder:text-mute";

/**
 * The search box above an admin table. Its label is read out but not shown,
 * unless `labelShown` puts it above the box.
 *
 * @param props - `label` names the box, `placeholder` is its hint, `value`
 *   is what was typed, `onChange` gets new text, and `labelShown` shows the
 *   label above the box (as on Users).
 * @returns The search box.
 */
export function SearchField({
  label,
  placeholder,
  value,
  onChange,
  labelShown = false,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  labelShown?: boolean;
}) {
  const input = (
    <input
      type="search"
      placeholder={placeholder}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={searchInput}
    />
  );
  if (labelShown) {
    return (
      <label className="flex max-w-[360px] flex-[1_1_280px] flex-col gap-1.5">
        <span className="text-[13px] text-soft">{label}</span>
        {input}
      </label>
    );
  }
  return (
    <label className="max-w-[360px] flex-[1_1_240px]">
      <span className="sr-only">{label}</span>
      {input}
    </label>
  );
}
