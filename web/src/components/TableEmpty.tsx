/**
 * The admin table template's state for when nothing has been logged yet: a
 * dashed box with a title and one line.
 *
 * @param props - `title` names what is missing; `body` says when it will
 *   appear.
 * @returns The empty state.
 */
export function TableEmpty({ title, body }: { title: string; body: string }) {
  return (
    <div className="box-border rounded-card border border-dashed border-line-strong px-6 py-[22px]">
      <div className="text-[16px] font-normal text-cream">{title}</div>
      <p className="mt-1.5 mb-0 text-[14px] text-soft">{body}</p>
    </div>
  );
}
