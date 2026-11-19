/**
 * Class names for one filter pill above an admin table, as the table
 * template draws it: cream when chosen, outlined otherwise.
 *
 * @param chosen - Whether the pill is the chosen (or switched on) one.
 * @returns The class names.
 */
export function filterPillClass(chosen: boolean): string {
  return `inline-flex min-h-11 cursor-pointer items-center rounded-pill border px-[18px] font-[inherit] text-[14px] no-underline ${
    chosen
      ? "border-cream bg-cream font-medium text-ink hover:text-ink"
      : "border-line-strong bg-transparent font-light text-text"
  }`;
}
