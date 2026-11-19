import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FilterPills } from "@/components/FilterPills";

describe("FilterPills", () => {
  it("marks the chosen pill and reports a new choice", async () => {
    const onChoose = vi.fn();
    const user = userEvent.setup();
    render(
      <FilterPills
        label="Outcome"
        options={[
          { id: "all", label: "All" },
          { id: "sent", label: "Sent" },
        ]}
        chosen="all"
        onChoose={onChoose}
      />,
    );

    expect(screen.getByRole("group", { name: "Outcome" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Sent" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await user.click(screen.getByRole("button", { name: "Sent" }));
    expect(onChoose).toHaveBeenCalledWith("sent");
  });
});
