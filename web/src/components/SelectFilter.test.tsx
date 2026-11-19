import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SelectFilter } from "@/components/SelectFilter";

const periods = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
];

describe("SelectFilter", () => {
  it("shows the chosen option in its box and reports a new one", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <SelectFilter
        label="Period"
        options={periods}
        value="7"
        onChange={onChange}
      />,
    );

    const select = screen.getByLabelText("Period");
    expect(select).toHaveValue("7");
    expect(screen.getAllByText("Last 7 days")).toHaveLength(2);

    await user.selectOptions(select, "30");
    expect(onChange).toHaveBeenCalledWith("30");
  });
});
