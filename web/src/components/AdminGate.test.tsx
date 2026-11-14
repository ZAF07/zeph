import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminGate } from "@/components/AdminGate";
import type { ApiClient } from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
};
const router = { replace: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

describe("AdminGate", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows the admin page to an Admin", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("admin"));

    renderWithQueries(<AdminGate>Admin page</AdminGate>);

    expect(await screen.findByText("Admin page")).toBeInTheDocument();
    expect(router.replace).not.toHaveBeenCalled();
  });

  it("sends a User who is not an Admin home without showing the page", async () => {
    apiClient.getMe.mockResolvedValue(userWithRole("user"));

    renderWithQueries(<AdminGate>Admin page</AdminGate>);

    await vi.waitFor(() => expect(router.replace).toHaveBeenCalledWith("/"));
    expect(screen.queryByText("Admin page")).not.toBeInTheDocument();
  });

  it("offers Try again when the role cannot be checked", async () => {
    apiClient.getMe
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(userWithRole("admin"));
    const user = userEvent.setup();
    renderWithQueries(<AdminGate>Admin page</AdminGate>);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Admin page")).toBeInTheDocument();
  });
});
