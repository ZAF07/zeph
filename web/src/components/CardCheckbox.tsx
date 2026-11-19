const boxClass = "size-[18px] flex-none cursor-pointer accent-cream";

/**
 * A tick box for a choice inside an open card's field row: with its own
 * words, or bare with an `id` when the row's title names it.
 *
 * @param props - `label` is the words, if any; `id` ties a bare box to the
 *   row's title; `checked` is whether it is ticked; `onChange` gets the new
 *   value.
 * @returns The tick box.
 */
export function CardCheckbox({
  label,
  id,
  checked,
  onChange,
}: {
  label?: string;
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  const box = (
    <input
      id={id}
      type="checkbox"
      checked={checked}
      onChange={(event) => onChange(event.target.checked)}
      className={boxClass}
    />
  );
  if (!label) {
    return <span className="inline-flex min-h-11 items-center">{box}</span>;
  }
  return (
    <label className="inline-flex min-h-11 cursor-pointer items-center gap-2 text-[15px] text-text">
      {box}
      {label}
    </label>
  );
}
