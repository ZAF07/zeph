import type { ReactNode } from "react";

/**
 * One column of an admin table: its heading, what each row shows in it, and
 * whether it is a main column (shown in the brighter text colour).
 */
export type TableColumn<Row> = {
  heading: string;
  cell: (row: Row) => ReactNode;
  isMain?: boolean;
};

/**
 * An admin table as it shows below 900px: each row is a card of label and
 * value lines, so nothing scrolls sideways. Hidden from 900px, where the
 * table shows instead.
 *
 * @param props - `columns` say what to show, `rows` are the rows and
 *   `rowKey` gives each row's key.
 * @returns The cards.
 */
export function TableCards<Row>({
  columns,
  rows,
  rowKey,
}: {
  columns: TableColumn<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
}) {
  return (
    <div className="flex flex-col gap-3 min-[900px]:hidden">
      {rows.map((row) => (
        <dl
          key={rowKey(row)}
          className="m-0 box-border rounded-tile border border-line bg-panel px-[18px] py-1.5"
        >
          {columns.map((column, index) => (
            <div
              key={column.heading}
              className={`box-content flex min-h-10 items-center justify-between gap-4 ${
                index > 0 ? "border-t border-line" : ""
              }`}
            >
              <dt className="flex-none text-[11px] font-medium tracking-[1.5px] text-soft uppercase">
                {column.heading}
              </dt>
              <dd className="m-0 min-w-0 text-right text-[14px] text-text">
                {column.cell(row)}
              </dd>
            </div>
          ))}
        </dl>
      ))}
    </div>
  );
}
