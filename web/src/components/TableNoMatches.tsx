/**
 * The admin table template's state for when the filters match nothing.
 *
 * @returns The note.
 */
export function TableNoMatches() {
  return (
    <div className="box-border rounded-card border border-line bg-panel px-[18px] py-4 text-[14px] text-soft">
      Nothing matches these filters.
    </div>
  );
}
