import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarNav } from "@/components/SidebarNav";
import type { ApiClient } from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  usePathname: () => "/admin/persona",
}));

const userItems = [{ id: "home", label: "Home", href: "/", iconPath: "M0 0" }];

describe("SidebarNav", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows the Admin group to an Admin, marking the page being viewed", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));

    render(<SidebarNav items={userItems} />);

    const adminGroup = await screen.findByRole("group", { name: "Admin" });
    const links = within(adminGroup).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "Users",
      "Persona",
      "Prompts & models",
      "Safety",
      "Safeguard Events",
      "Platform settings",
    ]);
    expect(
      within(adminGroup).getByRole("link", { name: "Persona" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("hides the Admin group from a User who is not an Admin", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    render(<SidebarNav items={userItems} />);

    await vi.waitFor(() => expect(apiClient.getMe).toHaveBeenCalled());
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Admin" })).toBeNull();
  });
});
