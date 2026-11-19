import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const isSignedIn = vi.fn<() => Promise<boolean>>();
const loadCopy = vi.fn<() => Promise<Copy | null>>();

vi.mock("@/lib/auth/server", () => ({ isSignedIn }));

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/DashboardFrame", () => ({
  DashboardFrame: ({ children }: { children: ReactNode }) => (
    <div data-testid="dashboard-frame">{children}</div>
  ),
}));

vi.mock("@/components/DashboardHome", () => ({
  DashboardHome: () => <p>Dashboard home</p>,
}));

const { default: RootPage, generateMetadata } = await import("@/app/page");

describe("the / page", () => {
  beforeEach(() => {
    isSignedIn.mockReset();
    loadCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("shows Landing, worded by Copy, when signed out", async () => {
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

  it("shows the error state when Copy can't be read", async () => {
    isSignedIn.mockResolvedValue(false);
    loadCopy.mockResolvedValue(null);

    render(await RootPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(screen.getByRole("button", { name: "Try again" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
  });

  it("takes Landing's tab title and search description from Copy", async () => {
    isSignedIn.mockResolvedValue(false);
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "landing.page_title": "Zeph, a thinking partner",
      "landing.page_description": "Talk it through with Zeph.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph, a thinking partner",
      description: "Talk it through with Zeph.",
    });
  });

  it("keeps the layout's title when Copy can't be read or someone is signed in", async () => {
    isSignedIn.mockResolvedValue(false);
    loadCopy.mockResolvedValue(null);
    expect(await generateMetadata()).toEqual({});

    isSignedIn.mockResolvedValue(true);
    expect(await generateMetadata()).toEqual({});
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
    expect(loadCopy).not.toHaveBeenCalled();
  });
});
