/**
 * Class names for a row of tabs, as the Memories page draws it. From 900px
 * up the row wraps; on a phone it scrolls sideways and never wraps.
 */
export const tabRow =
  "flex flex-nowrap gap-x-[22px] gap-y-1 overflow-x-auto border-b border-line min-[900px]:flex-wrap min-[900px]:gap-x-5 min-[900px]:overflow-x-visible";

/**
 * Class names for one tab: cream with a 2px cream underline when chosen.
 *
 * @param chosen - Whether the tab is the one shown.
 * @returns The class names.
 */
export function tabClass(chosen: boolean): string {
  return `inline-flex min-h-11 flex-none cursor-pointer items-center border-0 border-b-2 bg-transparent px-0.5 text-[14px] whitespace-nowrap no-underline min-[900px]:flex-initial ${
    chosen
      ? "border-cream font-normal text-cream hover:text-cream"
      : "border-transparent font-light text-soft"
  }`;
}
