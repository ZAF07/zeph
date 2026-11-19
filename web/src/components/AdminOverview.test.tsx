import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AdminOverview } from "@/components/AdminOverview";
import { overviewSample } from "@/lib/design-fixtures/overview";

describe("AdminOverview", () => {
  it("says the values are sample data", () => {
    render(<AdminOverview overview={overviewSample} />);

    expect(screen.getByText("Sample data")).toBeInTheDocument();
  });

  it("shows each count with its caption", () => {
    render(<AdminOverview overview={overviewSample} />);

    expect(screen.getByText("1,840")).toBeInTheDocument();
    expect(screen.getByText("limit 60 per user per day")).toBeInTheDocument();
    expect(screen.getByText("[BREAKDOWN BY PLAN]")).toBeInTheDocument();
  });

  it("tags the page title and Paying subscribers as To build", () => {
    render(<AdminOverview overview={overviewSample} />);

    expect(screen.getAllByText("To build")).toHaveLength(2);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "OverviewTo build",
    );
  });

  it("links each thing needing attention to its admin page", () => {
    render(<AdminOverview overview={overviewSample} />);

    const attention = screen.getByRole("region", { name: "Needs attention" });
    expect(
      within(attention).getByRole("link", { name: "Open Check-in Schedule" }),
    ).toHaveAttribute("href", "/admin/check-in-schedule");
    expect(
      within(attention).getByRole("link", { name: "Open Safeguard Events" }),
    ).toHaveAttribute("href", "/admin/safeguard-events");
  });

  it("shows which Features are on and links to the Features page", () => {
    render(<AdminOverview overview={overviewSample} />);

    const features = screen.getByRole("region", { name: "Features" });
    expect(within(features).getAllByText("On")).toHaveLength(2);
    expect(within(features).getByText("Off")).toBeInTheDocument();
    expect(
      within(features).getByRole("link", { name: "Open Features" }),
    ).toHaveAttribute("href", "/admin/features");
  });

  it("draws one bar per day and links the chart to Usage", () => {
    render(<AdminOverview overview={overviewSample} />);

    const chart = screen.getByRole("region", {
      name: "Messages, last 7 days",
    });
    expect(within(chart).getByText("Mon")).toBeInTheDocument();
    expect(
      within(chart).getByRole("link", { name: "Open Usage" }),
    ).toHaveAttribute("href", "/admin/usage");
  });

  it("sums up Knowledge and links to the Knowledge page", () => {
    render(<AdminOverview overview={overviewSample} />);

    const knowledge = screen.getByRole("region", { name: "Knowledge" });
    expect(within(knowledge).getByText("5 documents")).toBeInTheDocument();
    expect(
      within(knowledge).getByRole("link", { name: "Open Knowledge" }),
    ).toHaveAttribute("href", "/admin/knowledge");
  });
});
