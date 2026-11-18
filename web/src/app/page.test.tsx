import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const isSignedIn = vi.fn<() => Promise<boolean>>();

vi.mock("@/lib/auth/server", () => ({ isSignedIn }));

vi.mock("@/components/DashboardFrame", () => ({
  DashboardFrame: ({ children }: { children: ReactNode }) => (
    <div data-testid="dashboard-frame">{children}</div>
  ),
}));

vi.mock("@/components/DashboardHome", () => ({
  DashboardHome: () => <p>Dashboard home</p>,
}));

const { default: RootPage } = await import("@/app/page");

describe("the / page", () => {
  beforeEach(() => {
    isSignedIn.mockReset();
  });

  it("shows Landing when signed out", async () => {
    isSignedIn.mockResolvedValue(false);

    render(await RootPage());

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /Think Deeper, Live More Deliberately\./,
      }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Dashboard home")).not.toBeInTheDocument();
  });

  it("shows Home in the Dashboard frame when signed in", async () => {
    isSignedIn.mockResolvedValue(true);

    render(await RootPage());

    expect(screen.getByTestId("dashboard-frame")).toHaveTextContent(
      "Dashboard home",
    );
    expect(
      screen.queryByRole("heading", { name: /Think Deeper/ }),
    ).not.toBeInTheDocument();
  });
});
