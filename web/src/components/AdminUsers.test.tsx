import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminUsers } from "@/components/AdminUsers";
import { ApiError, type AdminUser, type ApiClient } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";
import { noPatterns } from "@/lib/users";

const apiClient = {
  listAdminUsers: vi.fn<ApiClient["listAdminUsers"]>(),
  changeUserRole: vi.fn<ApiClient["changeUserRole"]>(),
  listUserFeatures: vi.fn<ApiClient["listUserFeatures"]>(),
  listFeatures: vi.fn<ApiClient["listFeatures"]>(),
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
  move_outcome_count: 3,
  has_portrait: true,
  pattern_counts: { ...noPatterns, noticed: 3, suspected: 1, confirmed: 2 },
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
  move_outcome_count: 0,
  has_portrait: false,
  pattern_counts: noPatterns,
};

function rowFor(name: string): HTMLElement {
  const row = within(screen.getByRole("table")).getByText(name).closest("tr");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

async function openPanelFor(name: string) {
  const user = userEvent.setup();
  await screen.findByRole("table");
  await user.click(
    within(rowFor(name)).getByRole("button", { name: "Manage" }),
  );
  const panel = await screen.findByRole("region", { name });
  return { user, panel: within(panel) };
}

describe("AdminUsers", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listAdminUsers.mockResolvedValue([maya, ren]);
    apiClient.listUserFeatures.mockResolvedValue({
      features: [],
      personal_sticker_count: 0,
    });
    apiClient.listFeatures.mockResolvedValue([]);
  });

  it("lists each User with role, sign-up date, Telegram status and counts", async () => {
    renderWithQueries(<AdminUsers />);

    await screen.findByRole("table");
    const mayaRow = within(rowFor("Maya Lin"));
    expect(mayaRow.getByText("maya@example.com")).toBeInTheDocument();
    expect(mayaRow.getByText("Admin")).toBeInTheDocument();
    expect(mayaRow.getByText("2 Oct 2026")).toBeInTheDocument();
    expect(mayaRow.getByText("Connected")).toBeInTheDocument();
    expect(mayaRow.getByText("41")).toBeInTheDocument();
    expect(mayaRow.getByText("612")).toBeInTheDocument();
    expect(mayaRow.getByText("[PLAN]")).toBeInTheDocument();
    const renRow = within(rowFor("Ren Okafor"));
    expect(renRow.getByText("User")).toBeInTheDocument();
    expect(renRow.getByText("Not connected")).toBeInTheDocument();
    expect(screen.getByText("2 users · 1 admin")).toBeInTheDocument();
  });

  it("shows each User as a card of label and value lines for phones", async () => {
    renderWithQueries(<AdminUsers />);

    await screen.findByRole("table");
    const users = screen
      .getAllByRole("term")
      .filter((term) => term.textContent === "User")
      .map((term) => term.nextElementSibling?.textContent);
    expect(users).toEqual([
      "Maya Linmaya@example.com",
      "Ren Okaforren@example.com",
    ]);
  });

  it("finds Users by name or email", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);
    await screen.findByRole("table");

    await user.type(screen.getByLabelText("Search by name or email"), "ren@");

    const table = within(screen.getByRole("table"));
    expect(table.queryByText("Maya Lin")).toBeNull();
    expect(table.getByText("Ren Okafor")).toBeInTheDocument();
  });

  it("says when the search matches nobody", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AdminUsers />);
    await screen.findByRole("table");

    await user.type(screen.getByLabelText("Search by name or email"), "zz");

    expect(screen.getByText("Nothing matches these filters.")).toBeVisible();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("opens a User in the side panel only when Manage is pressed", async () => {
    renderWithQueries(<AdminUsers />);
    await screen.findByRole("table");
    expect(screen.queryByRole("region", { name: "Maya Lin" })).toBeNull();

    const { panel } = await openPanelFor("Maya Lin");

    expect(
      panel.getByText("maya@example.com · signed up 2 Oct 2026"),
    ).toBeInTheDocument();
    expect(panel.getByText("Life threads").nextSibling).toHaveTextContent("7");
    expect(panel.getByText("Confirmed Patterns").nextSibling).toHaveTextContent(
      "2",
    );
    expect(panel.getByText("Noticed Patterns").nextSibling).toHaveTextContent(
      "3",
    );
    expect(panel.getByText("Suspected Patterns").nextSibling).toHaveTextContent(
      "1",
    );
    expect(panel.queryByText("Closed Patterns")).toBeNull();
    expect(panel.getByText("Move outcomes").nextSibling).toHaveTextContent("3");
    expect(panel.getByText("Portrait").nextSibling).toHaveTextContent(
      "Written",
    );
    expect(
      panel.getByRole("link", { name: "Open this user in Check-in Schedule" }),
    ).toHaveAttribute(
      "href",
      "/admin/check-in-schedule?search=maya%40example.com",
    );
    expect(apiClient.listUserFeatures).toHaveBeenCalledWith("maya");
  });

  it("says when a User has no Portrait yet", async () => {
    renderWithQueries(<AdminUsers />);

    const { panel } = await openPanelFor("Ren Okafor");

    expect(panel.getByText("Portrait").nextSibling).toHaveTextContent(
      "Not written",
    );
    expect(panel.queryByText("Noticed Patterns")).toBeNull();
  });

  it("makes a User an Admin", async () => {
    apiClient.changeUserRole.mockResolvedValue({ id: "ren", role: "admin" });
    renderWithQueries(<AdminUsers />);

    const { user, panel } = await openPanelFor("Ren Okafor");
    await user.click(panel.getByRole("button", { name: "Make admin" }));

    expect(apiClient.changeUserRole).toHaveBeenCalledWith("ren", "admin");
    expect(await panel.findByText("Ren Okafor is now an Admin.")).toBeVisible();
    expect(
      panel.getByRole("button", { name: "Remove admin" }),
    ).toBeInTheDocument();
    expect(within(rowFor("Ren Okafor")).getByText("Admin")).toBeInTheDocument();
    expect(screen.getByText("2 users · 2 admins")).toBeInTheDocument();
  });

  it("explains when the last Admin can't be removed", async () => {
    apiClient.changeUserRole.mockRejectedValue(
      new ApiError(409, "/api/admin/users/maya/role"),
    );
    renderWithQueries(<AdminUsers />);

    const { user, panel } = await openPanelFor("Maya Lin");
    await user.click(panel.getByRole("button", { name: "Remove admin" }));

    expect(await panel.findByRole("alert")).toHaveTextContent(
      "Can’t remove Maya Lin: they’re the only Admin. Make someone else an Admin first, so the platform is never left without one.",
    );
    expect(within(rowFor("Maya Lin")).getByText("Admin")).toBeInTheDocument();
  });

  it("shows soft loading rows while the list loads", async () => {
    apiClient.listAdminUsers.mockReturnValue(new Promise(() => {}));

    renderWithQueries(<AdminUsers />);

    expect(
      await screen.findByRole("status", { name: "Loading users" }),
    ).toBeInTheDocument();
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

    expect(await screen.findByRole("table")).toBeInTheDocument();
  });
});
