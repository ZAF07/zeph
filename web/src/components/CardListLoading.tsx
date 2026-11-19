const barClass = "block rounded-[6px] bg-[rgba(255,255,255,.09)]";

/**
 * A card list while it loads: two folded rows of soft bars. No spinner.
 *
 * @param props - `label` names what is loading for screen readers.
 * @returns The loading list.
 */
export function CardListLoading({ label }: { label: string }) {
  return (
    <div role="status" aria-label={label} className="flex flex-col gap-3">
      {["first", "second"].map((row) => (
        <div
          key={row}
          className="box-border flex min-h-[68px] items-center gap-[14px] rounded-card border border-line bg-panel px-5 py-3"
        >
          <span aria-hidden="true" className={`${barClass} size-[18px]`} />
          <div className="flex flex-1 flex-col gap-2">
            <span aria-hidden="true" className={`${barClass} h-3.5 w-[34%]`} />
            <span aria-hidden="true" className={`${barClass} h-2.5 w-[70%]`} />
          </div>
        </div>
      ))}
    </div>
  );
}
