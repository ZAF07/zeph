/**
 * An orange annotation heading from a design reference, such as "How a
 * result reads, on a run". It is drawn only in design-fixture mode.
 *
 * @param props - `title` is the annotation's text.
 * @returns The heading row.
 */
export function DesignNote({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-3 border-t border-dashed border-line-strong pt-7 text-[11px] font-medium tracking-[2px] text-orange uppercase">
      {title}
    </div>
  );
}
