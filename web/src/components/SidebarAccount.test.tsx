import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarAccount } from "@/components/SidebarAccount";
import type { ApiClient } from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

describe("SidebarAccount", () => {
  beforeEach(() => {
    apiClient.getMe.mockReset();
  });

  it("shows the User's name, initial and email from /me", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(<SidebarAccount />);

    expect(await screen.findByText("Maya")).toBeInTheDocument();
    expect(screen.getByText("maya@example.com")).toBeInTheDocument();
    expect(screen.getByText("M")).toBeInTheDocument();
  });

  it("shows the email as the name when the User has no name", async () => {
    apiClient.getMe.mockResolvedValue({
      ...userWithRole("user"),
      name: null,
    });

    renderWithQueries(<SidebarAccount />);

    expect(await screen.findAllByText("maya@example.com")).toHaveLength(2);
  });

  it("shows a placeholder while /me loads", () => {
    apiClient.getMe.mockReturnValue(new Promise(() => {}));

    renderWithQueries(<SidebarAccount />);

    expect(screen.getByText("Loading your account")).toBeInTheDocument();
    expect(screen.queryByText("Maya")).not.toBeInTheDocument();
  });

  it("shows the Admin badge for an Admin", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));

    renderWithQueries(<SidebarAccount />);

    expect(await screen.findByText("Admin")).toBeInTheDocument();
  });
});
