import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlanDetails } from "@/components/PlanDetails";
import { planSample } from "@/lib/design-fixtures/plan";

describe("PlanDetails", () => {
  it("shows the drawn placeholders as they are", () => {
    render(<PlanDetails plan={planSample} />);

    expect(screen.getByText("Renews on [RENEWAL DATE].")).toBeInTheDocument();
    expect(screen.getByText("[N] of [DAILY LIMIT]")).toBeInTheDocument();
    expect(
      screen.getByText("[CARD BRAND] ending [LAST 4]"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("[PLAN NAME] · [AMOUNT]")).toHaveLength(3);
  });

  it("marks the User's plan and locks its button", () => {
    render(<PlanDetails plan={planSample} />);

    expect(screen.getByText("Your plan")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Current plan" })).toBeDisabled();
    expect(
      screen.getAllByRole("button", { name: "Switch to this plan" }),
    ).toHaveLength(2);
  });

  it("fills the usage bar to the share of messages used", () => {
    render(<PlanDetails plan={planSample} />);

    const bar = screen.getByRole("img", { name: "Messages used today" });
    expect(bar.firstElementChild).toHaveStyle({ width: "38%" });
  });

  it("lists each plan's inclusions", () => {
    render(<PlanDetails plan={planSample} />);

    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(3);
    const lists = screen.getAllByRole("list");
    expect(lists).toHaveLength(3);
    for (const list of lists) {
      expect(within(list).getAllByRole("listitem")).toHaveLength(3);
    }
  });

  it("offers a Cancel plan button", () => {
    render(<PlanDetails plan={planSample} />);

    expect(
      screen.getByRole("heading", { name: "Cancel plan" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel plan" }),
    ).toBeInTheDocument();
  });
});
