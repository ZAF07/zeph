import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ModelCallLog } from "@/components/ModelCallLog";
import type { AdminUser, ApiClient, ModelCallTrace } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listModelCallTraces: vi.fn<ApiClient["listModelCallTraces"]>(),
  listAdminUsers: vi.fn<ApiClient["listAdminUsers"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const users: AdminUser[] = [
  {
    id: "u1",
    name: "Maya Lin",
    email: "maya@example.com",
    role: "user",
    signed_up_at: "2026-11-01T10:00:00Z",
    telegram_connected: true,
    conversation_count: 3,
    messages_sent: 20,
    life_thread_count: 0,
  },
];

const traces: ModelCallTrace[] = [
  {
    trace_id: "t2",
    kind: "message",
    user_id: "u1",
    user_name: "Maya Lin",
    user_email: "maya@example.com",
    started_at: "2026-11-14T10:30:00Z",
    steps: ["safeguard", "safeguard", "reply"],
    tokens_in: 1200,
    tokens_out: 80,
    duration_ms: 2400,
    error_count: 1,
    has_content: false,
  },
  {
    trace_id: "t1",
    kind: "check_in",
    user_id: "u2",
    user_name: null,
    user_email: "owner@example.com",
    started_at: "2026-11-14T09:00:00Z",
    steps: ["check_in"],
    tokens_in: 500,
    tokens_out: 40,
    duration_ms: 850,
    error_count: 0,
    has_content: true,
  },
];

function rowTexts() {
  const rows = within(screen.getByRole("table")).getAllByRole("row");
  return rows.slice(1).map((row) =>
    within(row)
      .getAllByRole("cell")
      .slice(1)
      .map((cell) => cell.textContent),
  );
}

describe("ModelCallLog", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listModelCallTraces.mockResolvedValue(traces);
    apiClient.listAdminUsers.mockResolvedValue(users);
  });

  it("lists traces with steps, totals and errors, and links each to its page", async () => {
    renderWithQueries(<ModelCallLog />);

    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(apiClient.listModelCallTraces).toHaveBeenCalledWith({ days: 7 });
    expect(rowTexts()).toEqual([
      [
        "Maya Lin",
        "Message",
        "Safeguard ×2 → Reply",
        "1,200 in / 80 out",
        "2.4 s",
        "1 error",
        "None",
      ],
      [
        "owner@example.com",
        "Check-in",
        "Check-in",
        "500 in / 40 out",
        "850 ms",
        "—",
        "Full",
      ],
    ]);
    const [firstLink] = screen.getAllByRole("link");
    expect(firstLink).toHaveAttribute("href", "/admin/model-calls/t2");
  });

  it("asks the backend again for each filter", async () => {
    const user = userEvent.setup();
    renderWithQueries(<ModelCallLog />);
    await screen.findByRole("table");

    await user.selectOptions(
      await screen.findByRole("combobox", { name: "User" }),
      "u1",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Step" }),
      "reply",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Period" }),
      "30",
    );
    await user.click(screen.getByRole("button", { name: "Errors only" }));

    await waitFor(() =>
      expect(apiClient.listModelCallTraces).toHaveBeenLastCalledWith({
        userId: "u1",
        step: "reply",
        days: 30,
        errorsOnly: true,
      }),
    );
  });

  it("says when there are no traces yet", async () => {
    apiClient.listModelCallTraces.mockResolvedValue([]);

    renderWithQueries(<ModelCallLog />);

    expect(await screen.findByText("No model calls yet")).toBeInTheDocument();
  });

  it("offers Try again when the log can't be loaded", async () => {
    apiClient.listModelCallTraces.mockRejectedValue(new Error("down"));

    renderWithQueries(<ModelCallLog />);

    expect(
      await screen.findByText("Couldn’t load the Model Call Log"),
    ).toBeInTheDocument();
  });
});
