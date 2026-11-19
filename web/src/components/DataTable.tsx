import { LockIcon } from "@/components/LockIcon";
import { TableCards, type TableColumn } from "@/components/TableCards";

/**
 * The table of the admin table template. From 900px it is a table in a
 * panel, with an optional "No message content" caption. Below 900px each
 * row becomes a card of label and value lines, so nothing scrolls sideways.
 *
 * @param props - `columns` say what to show, `rows` are the rows,
 *   `rowKey` gives each row's key, `noMessageContent` adds the caption, and
 *   `minWidthClass` is the table's least width (e.g. `min-w-[820px]`), and
 *   `onRowClick`, when given, is called when a table row is clicked.
 * @returns The table and its phone cards.
 */
export function DataTable<Row>({
  columns,
  rows,
  rowKey,
  noMessageContent = false,
  minWidthClass,
  onRowClick,
}: {
  columns: TableColumn<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  noMessageContent?: boolean;
  minWidthClass: string;
  onRowClick?: (row: Row) => void;
}) {
  return (
    <>
      <div className="overflow-x-auto rounded-card border border-line bg-panel max-[899px]:hidden">
        <table className={`w-full border-collapse ${minWidthClass}`}>
          {noMessageContent ? (
            <caption className="border-b border-line px-[18px] py-2.5 text-left text-[12px] font-normal text-soft">
              <span className="inline-flex items-center gap-2">
                <LockIcon />
                No message content
              </span>
            </caption>
          ) : null}
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.heading}
                  scope="col"
                  className="border-b border-line px-[18px] py-3 text-left text-[11px] font-medium tracking-[1.5px] whitespace-nowrap text-soft uppercase"
                >
                  {column.heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`${index > 0 ? "border-t border-line" : ""} ${
                  onRowClick ? "cursor-pointer" : ""
                }`}
              >
                {columns.map((column) => (
                  <td
                    key={column.heading}
                    className={`px-[18px] py-[13px] text-[14px] ${
                      column.isMain ? "text-text" : "text-soft"
                    }`}
                  >
                    {column.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <TableCards columns={columns} rows={rows} rowKey={rowKey} />
    </>
  );
}
