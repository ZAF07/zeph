import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();
const checkInsCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/CheckInsSettings", () => ({
  CheckInsSettings: ({ copy }: { copy: Copy }) => {
    checkInsCopy(copy);
    return <h1>{copy["check_ins.hero.heading"]}</h1>;
  },
}));

const { default: CheckInsPage, generateMetadata } =
  await import("@/app/(dashboard)/(user)/check-ins/page");

describe("the /check-ins page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
    checkInsCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("gives the page only its own Copy slots and the frequency names", async () => {
    render(await CheckInsPage());

    expect(
      screen.getByRole("heading", { name: "Check-ins" }),
    ).toBeInTheDocument();
    const keys = Object.keys(checkInsCopy.mock.lastCall?.[0] ?? {});
    expect(keys.length).toBeGreaterThan(0);
    expect(
      keys.every(
        (key) =>
          key.startsWith("check_ins.") ||
          key.startsWith("onboarding.check_ins.frequency_"),
      ),
    ).toBe(true);
    expect(keys).toContain("onboarding.check_ins.frequency_weekly");
  });

  it("takes its browser tab title and description from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "check_ins.page_title": "Zeph — When Zeph says hello",
      "check_ins.page_description": "How often Zeph may message you first.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph — When Zeph says hello",
      description: "How often Zeph may message you first.",
    });
  });

  it("shows the couldn't-load block when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await CheckInsPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(checkInsCopy).not.toHaveBeenCalled();
    expect(await generateMetadata()).toEqual({});
  });
});
