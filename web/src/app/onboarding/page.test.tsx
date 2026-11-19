import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();
const flowCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/OnboardingFlow", () => ({
  OnboardingFlow: ({ copy }: { copy: Copy }) => {
    flowCopy(copy);
    return <h1>{copy["onboarding.hello.heading"]}</h1>;
  },
}));

const { default: OnboardingPage, generateMetadata } =
  await import("@/app/onboarding/page");

function renderPage() {
  return OnboardingPage({ searchParams: Promise.resolve({}) });
}

describe("the /onboarding page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("gives the onboarding steps the Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "onboarding.hello.heading": "Hi. I’m Zeph.",
    });

    render(await renderPage());

    expect(
      screen.getByRole("heading", { name: "Hi. I’m Zeph." }),
    ).toBeInTheDocument();
  });

  it("sends the browser only the slots onboarding shows", async () => {
    render(await renderPage());

    const keys = Object.keys(flowCopy.mock.lastCall?.[0] ?? {});
    expect(keys).toContain("onboarding.intentions.heading");
    expect(keys).toContain("connect_telegram.card.open_button");
    expect(keys).toContain("shared.wordmark");
    expect(keys.some((key) => key.startsWith("landing."))).toBe(false);
  });

  it("takes its tab title and description from Copy", async () => {
    expect(await generateMetadata()).toEqual({
      title: "Zeph — Onboarding",
      description: "A few questions so Zeph knows where to start.",
    });
  });

  it("shows the error state when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await renderPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(await generateMetadata()).toEqual({});
  });
});
