import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const isSignedIn = vi.fn<() => Promise<boolean>>();
const loadCopy = vi.fn<() => Promise<Copy | null>>();
const homeCopy = vi.fn<(copy: Copy) => void>();

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
  DashboardHome: ({ copy }: { copy: Copy }) => {
    homeCopy(copy);
    return <p>{copy["home.hero.eyebrow"]}</p>;
  },
}));

const { default: RootPage, generateMetadata } = await import("@/app/page");

describe("the / page", () => {
  beforeEach(() => {
    isSignedIn.mockReset();
    loadCopy.mockReset();
    homeCopy.mockReset();
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

  it("takes Home's tab title and search description from Copy when signed in", async () => {
    isSignedIn.mockResolvedValue(true);
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "home.page_title": "Zeph — Your day",
      "home.page_description": "Your Dashboard.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph — Your day",
      description: "Your Dashboard.",
    });
  });

  it("keeps the layout's title when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    isSignedIn.mockResolvedValue(false);
    expect(await generateMetadata()).toEqual({});
    isSignedIn.mockResolvedValue(true);
    expect(await generateMetadata()).toEqual({});
  });

  it("shows Home in the Dashboard frame when signed in, giving it only Home's slots", async () => {
    isSignedIn.mockResolvedValue(true);

    render(await RootPage());

    expect(screen.getByTestId("dashboard-frame")).toHaveTextContent("Home");
    expect(
      screen.queryByRole("heading", { name: /Think Deeper/ }),
    ).not.toBeInTheDocument();
    const keys = Object.keys(homeCopy.mock.lastCall?.[0] ?? {});
    expect(keys.length).toBeGreaterThan(0);
    expect(keys.every((key) => key.startsWith("home."))).toBe(true);
  });

  it("shows the error state, not Home, when signed in and Copy can't be read", async () => {
    isSignedIn.mockResolvedValue(true);
    loadCopy.mockResolvedValue(null);

    render(await RootPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(homeCopy).not.toHaveBeenCalled();
  });
});
