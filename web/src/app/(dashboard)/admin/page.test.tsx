import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AdminPage from "@/app/(dashboard)/admin/page";

describe("AdminPage", () => {
  it("shows the Overview instead of redirecting", () => {
    render(<AdminPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Overview",
    );
  });
});
