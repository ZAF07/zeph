/** One total above an admin table: what is counted and its value. */
export type StatTile = { label: string; value: string };

/**
 * The row of totals above an admin table, as the table template draws it,
 * in a region named "Totals". The tiles wrap onto more rows when there is
 * no room.
 *
 * @param props - `tiles` are the totals, in order.
 * @returns The totals.
 */
export function StatTiles({ tiles }: { tiles: StatTile[] }) {
  return (
    <section aria-label="Totals">
      <dl className="m-0 flex flex-wrap gap-4">
        {tiles.map((tile) => (
          <div
            key={tile.label}
            className="box-border min-w-0 flex-[1_1_150px] rounded-tile border border-line bg-panel px-5 py-4"
          >
            <dt className="text-[13px] text-soft">{tile.label}</dt>
            <dd className="m-0 mt-1 text-[26px] leading-[1.1] font-normal text-cream">
              {tile.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
