/** The soft bar colour, as drawn. */
const barClass = "block rounded-[6px] bg-[rgba(255,255,255,.09)]";

/** The bars for each panel shape: width and height classes, top to bottom. */
const barsByShape = {
  banner: ["w-[90px] h-[10px]", "w-[52%] h-[26px]", "w-[38%] h-[12px]"],
  card: [
    "w-[34%] h-[16px]",
    "w-[82%] h-[12px]",
    "w-[68%] h-[12px]",
    "w-[74%] h-[12px]",
  ],
};

/** The panel around the bars for each shape. */
const panelByShape = {
  banner: "min-h-[150px] gap-3.5 rounded-banner bg-bg-deep px-7 py-[26px]",
  card: "gap-4 rounded-card bg-panel px-6 py-[22px]",
};

/**
 * Soft bars in the shape of what is coming, inside the same panel. No
 * spinner.
 *
 * @param props - `shape` is a page `banner` or a `card` or list; `label`
 *   names what is loading for screen readers (for example "Loading memories").
 * @returns The loading panel.
 */
export function LoadingPanel({
  shape,
  label,
}: {
  shape: "banner" | "card";
  label: string;
}) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`flex flex-col border border-line ${panelByShape[shape]}`}
    >
      {barsByShape[shape].map((size) => (
        <span key={size} aria-hidden="true" className={`${barClass} ${size}`} />
      ))}
    </div>
  );
}
