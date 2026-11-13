import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminFeatures } from "@/components/AdminFeatures";
import type { ApiClient, FeatureSwitch } from "@/lib/api-client";

const apiClient = {
  listFeatures: vi.fn<ApiClient["listFeatures"]>(),
  setFeatureForEveryone: vi.fn<ApiClient["setFeatureForEveryone"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const webSearch: FeatureSwitch = {
  feature: "web_search",
  name: "Web Search",
  description: "Zeph can look things up on the web.",
  on: true,
  changed_by: null,
  changed_at: null,
};

function rowFor(name: string): HTMLElement {
  const row = screen.getByText(name).closest("li");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

describe("AdminFeatures", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listFeatures.mockResolvedValue([webSearch]);
  });

  it("lists each Feature with its description, switch and last change", async () => {
    render(<AdminFeatures />);

    await screen.findByText("Web Search");
    const row = within(rowFor("Web Search"));
    expect(row.getByText("Zeph can look things up on the web.")).toBeVisible();
    expect(
      row.getByRole("switch", { name: "Web Search for everyone" }),
    ).toHaveAttribute("aria-checked", "true");
    expect(row.getByText("Never changed")).toBeVisible();
  });

  it("shows who changed a switch last and when", async () => {
    apiClient.listFeatures.mockResolvedValue([
      {
        ...webSearch,
        on: false,
        changed_by: "maya@example.com",
        changed_at: "2026-11-13T09:00:00Z",
      },
    ]);
    render(<AdminFeatures />);

    await screen.findByText("Web Search");
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    expect(row.getByText(/13 Nov, .* by maya@example\.com/)).toBeVisible();
  });

  it("turns a Feature off for everyone and shows the new last change", async () => {
    apiClient.setFeatureForEveryone.mockResolvedValue({
      ...webSearch,
      on: false,
      changed_by: "owner@example.com",
      changed_at: "2026-11-13T10:00:00Z",
    });
    const user = userEvent.setup();
    render(<AdminFeatures />);

    await user.click(
      await screen.findByRole("switch", { name: "Web Search for everyone" }),
    );

    expect(apiClient.setFeatureForEveryone).toHaveBeenCalledWith(
      "web_search",
      false,
    );
    const row = within(rowFor("Web Search"));
    expect(row.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    expect(
      await row.findByText(/13 Nov, .* by owner@example\.com/),
    ).toBeVisible();
  });

  it("keeps the switch as it was when the change fails", async () => {
    apiClient.setFeatureForEveryone.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<AdminFeatures />);

    await user.click(
      await screen.findByRole("switch", { name: "Web Search for everyone" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t change Web Search. It is still on.",
    );
    expect(
      screen.getByRole("switch", { name: "Web Search for everyone" }),
    ).toHaveAttribute("aria-checked", "true");
  });

  it("offers Try again when the Features can't be loaded", async () => {
    apiClient.listFeatures.mockRejectedValueOnce(new Error("down"));
    const user = userEvent.setup();
    render(<AdminFeatures />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Web Search")).toBeVisible();
  });
});
