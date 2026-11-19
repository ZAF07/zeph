import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();
const memoriesCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/Memories", () => ({
  Memories: ({ copy }: { copy: Copy }) => {
    memoriesCopy(copy);
    return <h1>{copy["memories.hero.heading"]}</h1>;
  },
}));

const { default: MemoriesPage, generateMetadata } =
  await import("@/app/(dashboard)/(user)/memories/page");

describe("the /memories page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
    memoriesCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("gives the page only its own Copy slots and the Shared Memory-off notes", async () => {
    render(await MemoriesPage());

    expect(
      screen.getByRole("heading", { name: "Memories" }),
    ).toBeInTheDocument();
    const keys = Object.keys(memoriesCopy.mock.lastCall?.[0] ?? {});
    expect(keys.length).toBeGreaterThan(0);
    expect(keys).toContain("shared.memory_off.paused_title");
    expect(
      keys.every(
        (key) =>
          key.startsWith("memories.") || key.startsWith("shared.memory_off."),
      ),
    ).toBe(true);
  });

  it("takes its browser tab title and description from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "memories.page_title": "Zeph — What I remember",
      "memories.page_description": "Everything Zeph keeps about you.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph — What I remember",
      description: "Everything Zeph keeps about you.",
    });
  });

  it("shows the couldn't-load block when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await MemoriesPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(memoriesCopy).not.toHaveBeenCalled();
    expect(await generateMetadata()).toEqual({});
  });
});
