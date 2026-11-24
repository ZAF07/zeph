import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarNav } from "@/components/SidebarNav";
import type { ApiClient } from "@/lib/api-client";
import { seedCopy } from "@/test/copy";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
const navigation = vi.hoisted(() => ({ pathname: "/admin/persona" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
}));

describe("SidebarNav", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    navigation.pathname = "/admin/persona";
  });

  it("shows the Admin group to an Admin, marking the page being viewed", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));

    renderWithQueries(<SidebarNav copy={seedCopy()} />);

    const adminGroup = await screen.findByRole("group", { name: "Admin" });
    const links = within(adminGroup).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "OverviewTo build",
      "Users",
      "Persona",
      "Prompts & models",
      "Safety",
      "Safeguard Events",
      "Knowledge",
      "Memory Categories",
      "Needs",
      "Moves",
      "Pattern Catalog",
      "Check-in Kinds",
      "Check-in log",
      "Check-in Schedule",
      "Sticker Library",
      "Features",
      "Platform settings",
      "Copy",
      "Usage",
      "Model call log",
      "Evals",
      "PlansTo build",
    ]);
    expect(
      within(adminGroup).getByRole("link", { name: "Persona" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("keeps an admin link marked on the pages under it", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));
    navigation.pathname = "/admin/knowledge/letters";

    renderWithQueries(<SidebarNav copy={seedCopy()} />);

    const adminGroup = await screen.findByRole("group", { name: "Admin" });
    expect(
      within(adminGroup).getByRole("link", { name: "Knowledge" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("hides the Admin group from a User who is not an Admin", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(<SidebarNav copy={seedCopy()} />);

    await vi.waitFor(() => expect(apiClient.getMe).toHaveBeenCalled());
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Admin" })).toBeNull();
  });
});
