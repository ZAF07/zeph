/**
 * A coloured pill for an Eval Run's state or a Case Result's outcome.
 *
 * @param props - `label` is the text; `pill` the colour classes.
 * @returns The pill.
 */
export function EvalPill({ label, pill }: { label: string; pill: string }) {
  return (
    <span
      className={`inline-flex w-fit items-center whitespace-nowrap rounded-full px-2.5 py-[3px] text-xs font-medium ${pill}`}
    >
      {label}
    </span>
  );
}
