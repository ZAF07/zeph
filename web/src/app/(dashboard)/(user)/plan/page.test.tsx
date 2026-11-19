import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PlanPage from "@/app/(dashboard)/(user)/plan/page";

describe("PlanPage", () => {
  it("tags the page title as To build and shows the drawn plan", () => {
    render(<PlanPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "PlanTo build",
    );
    expect(
      screen.getByText(
        "What you are on, what it includes and how you are billed.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Renews on [RENEWAL DATE].")).toBeInTheDocument();
  });
});
