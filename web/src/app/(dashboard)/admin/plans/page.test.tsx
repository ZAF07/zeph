import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AdminPlansPage from "@/app/(dashboard)/admin/plans/page";

describe("AdminPlansPage", () => {
  it("shows the To build empty state", () => {
    render(<AdminPlansPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "PlansTo build",
    );
    expect(screen.getByText("No plans yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Plans and billing aren’t built yet. This page will list them once they are.",
      ),
    ).toBeInTheDocument();
  });
});
