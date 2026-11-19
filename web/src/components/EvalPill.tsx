/**
 * A pill for an Eval Run's state or a Case Result's outcome, drawn as the
 * admin table's status pill.
 *
 * @param props - `label` is the text; `pill` the look's classes.
 * @returns The pill.
 */
export function EvalPill({ label, pill }: { label: string; pill: string }) {
  return (
    <span
      className={`inline-flex w-fit items-center rounded-pill px-2.5 py-0.5 text-[12px] font-normal whitespace-nowrap ${pill}`}
    >
      {label}
    </span>
  );
}
