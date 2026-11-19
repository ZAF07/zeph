import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const isSignedIn = vi.fn<() => Promise<boolean>>();
const loadCopy = vi.fn<() => Promise<Copy | null>>();
const shellCopy = vi.fn<(copy: Copy) => void>();
const gateCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/auth/server", () => ({ isSignedIn }));

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/headers", () => ({
  cookies: () => Promise.resolve({ get: () => undefined }),
}));

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/DashboardShell", () => ({
  DashboardShell: ({ copy, children }: { copy: Copy; children: ReactNode }) => {
    shellCopy(copy);
    return <div>{children}</div>;
  },
}));

vi.mock("@/components/OnboardingGate", () => ({
  OnboardingGate: ({ copy, children }: { copy: Copy; children: ReactNode }) => {
    gateCopy(copy);
    return <>{children}</>;
  },
}));

const { DashboardFrame } = await import("@/components/DashboardFrame");

describe("DashboardFrame", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isSignedIn.mockResolvedValue(true);
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("gives the menu and the gate only the frame's Copy slots", async () => {
    render(await DashboardFrame({ children: <p>Page content</p> }));

    expect(screen.getByText("Page content")).toBeInTheDocument();
    const keys = Object.keys(shellCopy.mock.lastCall?.[0] ?? {});
    expect(keys).toContain("shared.dashboard.home");
    expect(keys).toContain("shared.wordmark");
    expect(
      keys.every(
        (key) =>
          key.startsWith("shared.dashboard.") || key === "shared.wordmark",
      ),
    ).toBe(true);
    expect(gateCopy.mock.lastCall?.[0]).toEqual(shellCopy.mock.lastCall?.[0]);
  });

  it("shows the error state in place of the frame and page when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await DashboardFrame({ children: <p>Page content</p> }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(screen.queryByText("Page content")).not.toBeInTheDocument();
    expect(shellCopy).not.toHaveBeenCalled();
  });
});
