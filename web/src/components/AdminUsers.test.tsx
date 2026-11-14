import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminUsers } from "@/components/AdminUsers";
import { ApiError, type AdminUser, type ApiClient } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listAdminUsers: vi.fn<ApiClient["listAdminUsers"]>(),
  changeUserRole: vi.fn<ApiClient["changeUserRole"]>(),
  listUserFeatures: vi.fn<ApiClient["listUserFeatures"]>(),
  setFeatureForUser: vi.fn<ApiClient["setFeatureForUser"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const maya: AdminUser = {
  id: "maya",
  name: "Maya Lin",
  email: "maya@example.com",
  role: "admin",
  signed_up_at: "2026-10-02T09:00:00Z",
  telegram_connected: true,
  conversation_count: 41,
  messages_sent: 612,
  life_thread_count: 7,
  has_portrait: true,
};

const ren: AdminUser = {
  id: "ren",
  name: "Ren Okafor",
  email: "ren@example.com",
  role: "user",
  signed_up_at: "2026-10-05T09:00:00Z",
  telegram_connected: false,
  conversation_count: 0,
  messages_sent: 0,
  life_thread_count: 0,
  has_portrait: false,
};

function rowFor(name: string): HTMLElement {
  const row = screen.getByText(name).closest("tr");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

describe("AdminUsers", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listAdminUsers.mockResolvedValue([maya, ren]);
  });

  it("lists each User with sign-up date, Telegram status and counts", async () => {
    renderWithQueries(<AdminUsers />);

    await screen.findByText("Maya Lin");
    const mayaRow = within(rowFor("Maya Lin"));
    expect(mayaRow.getByText("maya@example.com")).toBeInTheDocument();
    expect(mayaRow.getByText("2 Oct 2026")).toBeInTheDocument();
    expect(mayaRow.getByText("Connected")).toBeInTheDocument();
    expect(mayaRow.getByText("41")).toBeInTheDocument();
    expect(mayaRow.getByText("612")).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Life Threads" }),
    ).toBeInTheDocument();
    expect(mayaRow.getByText("7")).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Portrait" }),
    ).toBeInTheDocument();
    expect(mayaRow.getByText("Yes")).toBeInTheDocument();
    expect(within(rowFor("Ren Okafor")).getByText("No")).toBeInTheDocument();
    expect(mayaRow.getByText("Admin")).toBeInTheDocument();
    expect(
      within(rowFor("Ren Okafor")).getByText("Not connected"),
    ).toBeVisible();
    expect(
      screen.getByText(/No message content · 1 Admin · 2 Users/),
    ).toBeVisible();
  });

  it("makes a User an Admin", async () => {
    apiClient.changeUserRole.mockResolvedValue({ id: "ren", role: "admin" });
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);

    await user.click(
      within(rowFor(await textOf("Ren Okafor"))).getByRole("button", {
        name: "Make Admin",
      }),
    );

    expect(apiClient.changeUserRole).toHaveBeenCalledWith("ren", "admin");
    expect(
      await screen.findByText("Ren Okafor is now an Admin."),
    ).toBeVisible();
    expect(
      within(rowFor("Ren Okafor")).getByRole("button", {
        name: "Remove Admin",
      }),
    ).toBeInTheDocument();
  });

  it("opens a User's Features panel from their row", async () => {
    apiClient.listUserFeatures.mockResolvedValue({
      features: [
        {
          feature: "web_search",
          name: "Web Search",
          works: true,
          reason: "on_for_everyone",
          switch: "default",
          changed_by_email: null,
          changed_at: null,
        },
      ],
      personal_sticker_count: 0,
    });
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);

    await user.click(
      within(rowFor(await textOf("Ren Okafor"))).getByRole("button", {
        name: "Features",
      }),
    );

    const dialog = await screen.findByRole("dialog", {
      name: "Features for Ren Okafor",
    });
    expect(apiClient.listUserFeatures).toHaveBeenCalledWith("ren");
    expect(await within(dialog).findByText("Web Search")).toBeVisible();
    await user.click(within(dialog).getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("explains when the last Admin can't be removed", async () => {
    apiClient.changeUserRole.mockRejectedValue(
      new ApiError(409, "/api/admin/users/maya/role"),
    );
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);

    await user.click(
      within(rowFor(await textOf("Maya Lin"))).getByRole("button", {
        name: "Remove Admin",
      }),
    );

    expect(
      await screen.findByText(
        "Can’t remove Maya Lin: they’re the only Admin. Make someone else an Admin first, so the platform is never left without one.",
      ),
    ).toBeVisible();
    expect(within(rowFor("Maya Lin")).getByText("Admin")).toBeInTheDocument();
  });

  it("finds Users by name or email and filters by Admins or Telegram", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);
    await screen.findByText("Maya Lin");

    await user.type(screen.getByLabelText("Search users"), "ren@");
    expect(screen.queryByText("Maya Lin")).toBeNull();
    expect(screen.getByText("Ren Okafor")).toBeVisible();

    await user.clear(screen.getByLabelText("Search users"));
    await user.click(screen.getByRole("button", { name: "Admins" }));
    expect(screen.getByText("Maya Lin")).toBeVisible();
    expect(screen.queryByText("Ren Okafor")).toBeNull();

    await user.click(
      screen.getByRole("button", { name: "Telegram not connected" }),
    );
    expect(screen.queryByText("Maya Lin")).toBeNull();
    expect(screen.getByText("Ren Okafor")).toBeVisible();
  });

  it("shows an empty state before anyone signs up", async () => {
    apiClient.listAdminUsers.mockResolvedValue([]);

    renderWithQueries(<AdminUsers />);

    expect(await screen.findByText("No users yet")).toBeVisible();
  });

  it("offers Try again when the list cannot be loaded", async () => {
    apiClient.listAdminUsers
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue([maya]);
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Maya Lin")).toBeVisible();
  });
});

async function textOf(text: string): Promise<string> {
  await screen.findByText(text);
  return text;
}
