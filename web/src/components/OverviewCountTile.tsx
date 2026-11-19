import { ToBuildTag } from "@/components/ToBuildTag";
import type { OverviewCount } from "@/lib/design-fixtures/overview";

/**
 * One count at the top of the admin Overview: what is counted, the number
 * and a line under it. A count with no backend yet carries the "To build"
 * tag.
 *
 * @param props - `count` is the count to draw.
 * @returns The tile.
 */
export function OverviewCountTile({ count }: { count: OverviewCount }) {
  return (
    <div className="box-border min-w-0 flex-[1_1_170px] rounded-card border border-line bg-panel px-[22px] py-5">
      <div className="flex items-center text-[13px] text-soft">
        {count.label}
        {count.isToBuild ? <ToBuildTag /> : null}
      </div>
      <div className="mt-1.5 mb-0.5 text-[32px] leading-[1.1] font-normal text-cream">
        {count.value}
      </div>
      <div className="text-[12px] text-soft">{count.caption}</div>
    </div>
  );
}
