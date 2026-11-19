import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();
const accountCopy = vi.fn<(copy: Copy) => void>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@/components/AccountSettings", () => ({
  AccountSettings: ({ copy }: { copy: Copy }) => {
    accountCopy(copy);
    return null;
  },
}));

const { default: AccountPage, generateMetadata } =
  await import("@/app/(dashboard)/(user)/account/page");

describe("the /account page", () => {
  beforeEach(() => {
    loadCopy.mockReset();
    accountCopy.mockReset();
    loadCopy.mockResolvedValue(seedCopy());
  });

  it("shows its heading from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "account.header.heading": "You and your data",
    });

    render(await AccountPage());

    expect(
      screen.getByRole("heading", { name: "You and your data" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Your details, what Zeph is allowed to keep, and how to remove it.",
      ),
    ).toBeInTheDocument();
  });

  it("gives the settings only its own Copy slots and the location labels", async () => {
    render(await AccountPage());

    const keys = Object.keys(accountCopy.mock.lastCall?.[0] ?? {});
    expect(keys).toContain("account.profile.heading");
    expect(keys).toContain("onboarding.location.country_label");
    expect(
      keys.every(
        (key) =>
          key.startsWith("account.") || key.startsWith("onboarding.location."),
      ),
    ).toBe(true);
  });

  it("takes its browser tab title and description from Copy", async () => {
    loadCopy.mockResolvedValue({
      ...seedCopy(),
      "account.page_title": "Zeph — Your account",
      "account.page_description": "Your details and your data.",
    });

    expect(await generateMetadata()).toEqual({
      title: "Zeph — Your account",
      description: "Your details and your data.",
    });
  });

  it("shows the couldn't-load block when Copy can't be read", async () => {
    loadCopy.mockResolvedValue(null);

    render(await AccountPage());

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t load this page",
    );
    expect(accountCopy).not.toHaveBeenCalled();
    expect(await generateMetadata()).toEqual({});
  });
});
