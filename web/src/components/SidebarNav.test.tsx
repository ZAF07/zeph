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
const navigation = vi.hoisted(() => ({ pathname: "/admin/persona" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
}));

const userItems = [{ id: "home", label: "Home", href: "/", iconPath: "M0 0" }];

describe("SidebarNav", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    navigation.pathname = "/admin/persona";
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
      "Knowledge",
      "Memory Categories",
      "Check-in Kinds",
      "Check-in log",
      "Sticker Library",
      "Features",
      "Platform settings",
      "Usage",
    ]);
    expect(
      within(adminGroup).getByRole("link", { name: "Persona" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("keeps an admin link marked on the pages under it", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));
    navigation.pathname = "/admin/knowledge/letters";

    render(<SidebarNav items={userItems} />);

    const adminGroup = await screen.findByRole("group", { name: "Admin" });
    expect(
      within(adminGroup).getByRole("link", { name: "Knowledge" }),
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
