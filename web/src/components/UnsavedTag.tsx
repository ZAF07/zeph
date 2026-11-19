/**
 * The orange "Unsaved changes" tag, shown while there are edits not yet
 * saved.
 *
 * @returns The tag.
 */
export function UnsavedTag() {
  return (
    <span className="rounded-pill border border-orange px-3 py-[3px] text-[12px] font-normal text-orange">
      Unsaved changes
    </span>
  );
}
