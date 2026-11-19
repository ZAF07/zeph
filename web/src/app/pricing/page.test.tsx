import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

const { default: PricingPage, generateMetadata } =
  await import("@/app/pricing/page");

describe("the /pricing page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
  });

  it("shows the plans worded by Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "pricing.plus.button": "Try Plus",
    });

    render(await PricingPage());

    expect(screen.getByRole("link", { name: "Try Plus" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("takes its tab title and description from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "pricing.page_title": "Zeph plans",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph plans",
      description: seedCopy()["pricing.page_description"],
    });
  });

  it("shows the error state when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await PricingPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
  });
});
