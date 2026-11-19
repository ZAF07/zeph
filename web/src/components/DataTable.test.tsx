import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataTable } from "@/components/DataTable";
import type { TableColumn } from "@/components/TableCards";

type Row = { id: string; name: string; count: number };

const rows: Row[] = [
  { id: "a", name: "Alex", count: 3 },
  { id: "b", name: "Priya", count: 0 },
];

const columns: TableColumn<Row>[] = [
  { heading: "Name", isMain: true, cell: (row) => row.name },
  { heading: "Count", cell: (row) => row.count },
];

describe("DataTable", () => {
  it("shows a table with a heading per column and a row per item", () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        minWidthClass="min-w-[400px]"
      />,
    );

    const table = within(screen.getByRole("table"));
    expect(
      table.getAllByRole("columnheader").map((head) => head.textContent),
    ).toEqual(["Name", "Count"]);
    expect(
      table
        .getAllByRole("row")
        .slice(1)
        .map((row) => row.textContent),
    ).toEqual(["Alex3", "Priya0"]);
    expect(screen.queryByText("No message content")).toBeNull();
  });

  it("adds the No message content caption when asked", () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        noMessageContent
        minWidthClass="min-w-[400px]"
      />,
    );

    expect(
      within(screen.getByRole("table")).getByText("No message content"),
    ).toBeInTheDocument();
  });

  it("also shows each row as a card of label and value lines for phones", () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        minWidthClass="min-w-[400px]"
      />,
    );

    const lines = screen
      .getAllByRole("term")
      .map((term) => `${term.textContent}: ${term.nextSibling?.textContent}`);
    expect(lines).toEqual([
      "Name: Alex",
      "Count: 3",
      "Name: Priya",
      "Count: 0",
    ]);
  });
});
