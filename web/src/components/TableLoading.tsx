/** The soft bar colour, as drawn. */
const barClass = "block rounded-[6px] bg-[rgba(255,255,255,.09)]";

/** The bars in each loading row: width and height classes, left to right. */
const rowBars = [
  "w-[18%] h-[12px]",
  "w-[14%] h-[12px]",
  "w-[9%] h-[18px]",
  "w-[22%] h-[12px]",
];

/**
 * The admin table template's loading state: three rows of soft bars in the
 * table's panel. No spinner.
 *
 * @param props - `label` names what is loading for screen readers (for
 *   example "Loading log").
 * @returns The loading rows.
 */
export function TableLoading({ label }: { label: string }) {
  return (
    <div
      role="status"
      aria-label={label}
      className="box-border rounded-card border border-line bg-panel px-[18px] py-1.5"
    >
      {[0, 1, 2].map((row) => (
        <div
          key={row}
          className={`box-content flex min-h-12 items-center gap-6 ${
            row > 0 ? "border-t border-line" : ""
          }`}
        >
          {rowBars.map((size) => (
            <span
              key={size}
              aria-hidden="true"
              className={`${barClass} ${size}`}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
