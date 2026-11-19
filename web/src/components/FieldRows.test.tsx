import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FieldRow } from "@/components/FieldRow";
import { FieldRows } from "@/components/FieldRows";

describe("FieldRows", () => {
  it("draws the panel box, the rows with lines between, and the footnote", () => {
    render(
      <FieldRows footnote="Using the starting values">
        <FieldRow
          title="Daily message limit"
          caption="Per user, per day."
          htmlFor="limit"
        >
          <input id="limit" />
        </FieldRow>
        <FieldRow title="Web search">
          <span>switch</span>
        </FieldRow>
      </FieldRows>,
    );

    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveClass("py-4", "border-t", "first:border-t-0");
    expect(rows[0]?.parentElement?.parentElement).toHaveClass(
      "rounded-card",
      "bg-panel",
      "px-6",
      "py-1",
    );
    expect(screen.getByLabelText("Daily message limit")).toBe(
      screen.getByRole("textbox"),
    );
    expect(screen.getByText("Daily message limit")).toHaveClass(
      "text-[15px]",
      "text-text",
    );
    expect(screen.getByText("Per user, per day.")).toHaveClass(
      "text-[13px]",
      "text-soft",
    );
    expect(screen.getByText("Using the starting values")).toHaveClass(
      "pb-3.5",
      "text-[12px]",
      "text-soft",
    );
  });
});
