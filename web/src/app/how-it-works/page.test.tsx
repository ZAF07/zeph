import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

const { default: HowItWorksPage, generateMetadata } =
  await import("@/app/how-it-works/page");

describe("the /how-it-works page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
  });

  it("shows How It Works worded by Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "how_it_works.hero.eyebrow": "The steps",
    });

    render(await HowItWorksPage());

    expect(screen.getByText("The steps")).toBeInTheDocument();
  });

  it("takes its tab title and description from Copy", async () => {
    loadCopy.mockResolvedValue(seedCopy());

    expect(await generateMetadata()).toEqual({
      title: "Zeph — How it works",
      description: seedCopy()["how_it_works.page_description"],
    });
  });

  it("shows the error state when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await HowItWorksPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(await generateMetadata()).toEqual({});
  });
});
