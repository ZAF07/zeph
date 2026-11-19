import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarAccount } from "@/components/SidebarAccount";
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

describe("SidebarAccount", () => {
  beforeEach(() => {
    apiClient.getMe.mockReset();
  });

  it("shows the User's name and email from /me", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(<SidebarAccount copy={seedCopy()} />);

    expect(await screen.findByText("Maya")).toBeInTheDocument();
    expect(screen.getByText("maya@example.com")).toBeInTheDocument();
  });

  it("keeps the full name and email on hover, for when they are cut short", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(<SidebarAccount copy={seedCopy()} />);

    expect(await screen.findByText("Maya")).toHaveAttribute("title", "Maya");
    expect(screen.getByText("maya@example.com")).toHaveAttribute(
      "title",
      "maya@example.com",
    );
  });

  it("shows the email as the name when the User has no name", async () => {
    apiClient.getMe.mockResolvedValue({
      ...userWithRole("user"),
      name: null,
    });

    renderWithQueries(<SidebarAccount copy={seedCopy()} />);

    expect(await screen.findAllByText("maya@example.com")).toHaveLength(2);
  });

  it("shows a placeholder while /me loads", () => {
    apiClient.getMe.mockReturnValue(new Promise(() => {}));

    renderWithQueries(<SidebarAccount copy={seedCopy()} />);

    expect(screen.getByText("Loading your account")).toBeInTheDocument();
    expect(screen.queryByText("Maya")).not.toBeInTheDocument();
  });

  it("shows Admin in place of the email for an Admin", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));

    renderWithQueries(<SidebarAccount copy={seedCopy()} />);

    expect(await screen.findByText("Admin")).toBeInTheDocument();
    expect(screen.queryByText("maya@example.com")).toBeNull();
  });

  it("puts the given action at the end of the row", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(
      <SidebarAccount copy={seedCopy()} action={<button>Sign out</button>} />,
    );

    expect(
      await screen.findByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
  });
});
