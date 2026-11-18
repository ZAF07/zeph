/**
 * The orange "To build" tag, put after the name of a feature that has no
 * backend yet.
 *
 * @returns The tag.
 */
export function ToBuildTag() {
  return (
    <span className="ml-2 rounded-pill border border-orange px-2 py-px text-[10px] font-medium tracking-[0.5px] text-orange uppercase">
      To build
    </span>
  );
}
