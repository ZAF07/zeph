import type { ReactNode } from "react";

/**
 * The small uppercase label with a short line before it, from the design's
 * public pages.
 *
 * @param props - `children` is the label.
 * @returns The label.
 */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center gap-3 text-[11px] font-medium tracking-[2.5px] text-soft uppercase">
      <span aria-hidden="true" className="h-px w-[18px] bg-soft" />
      {children}
    </div>
  );
}
