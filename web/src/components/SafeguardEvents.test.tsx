import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafeguardEvents } from "@/components/SafeguardEvents";
import type { ApiClient, SafeguardEvent } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listSafeguardEvents: vi.fn<ApiClient["listSafeguardEvents"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const tom: SafeguardEvent = {
  id: "event-1",
  user_id: "tom",
  user_name: "Tom Hale",
  user_email: "tom@example.com",
  risk_type: "suicide_or_self_harm",
  created_at: "2026-11-10T15:41:00Z",
  helplines_country: "GB",
};

const ren: SafeguardEvent = {
  id: "event-2",
  user_id: "ren",
  user_name: null,
  user_email: "ren@example.com",
  risk_type: "abuse",
  created_at: "2026-10-29T11:02:00Z",
  helplines_country: null,
};

describe("SafeguardEvents", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listSafeguardEvents.mockResolvedValue([tom, ren]);
  });

  it("lists who, when and what kind of risk, never message content", async () => {
    renderWithQueries(<SafeguardEvents />);

    const tomRow = within((await screen.findByText("Tom Hale")).closest("tr")!);
    expect(tomRow.getByText("Suicide / self-harm")).toBeInTheDocument();
    expect(tomRow.getByText("Sent")).toBeInTheDocument();
    expect(tomRow.getByText("United Kingdom")).toBeInTheDocument();
    expect(tomRow.getByText(/10 Nov, \d\d:\d\d/)).toBeInTheDocument();
    const renRow = within(screen.getByText("ren@example.com").closest("tr")!);
    expect(renRow.getByText("International fallback")).toBeInTheDocument();
    expect(
      screen.getByText(/No message content · 2 events in the last 30 days/),
    ).toBeVisible();
    expect(apiClient.listSafeguardEvents).toHaveBeenCalledWith({
      riskType: undefined,
      days: 30,
    });
  });

  it("filters by risk type and period", async () => {
    const user = userEvent.setup();
    renderWithQueries(<SafeguardEvents />);
    await screen.findByText("Tom Hale");

    await user.click(screen.getByRole("button", { name: "Abuse" }));
    await user.selectOptions(screen.getByLabelText("Period"), "All time");

    expect(apiClient.listSafeguardEvents).toHaveBeenLastCalledWith({
      riskType: "abuse",
      days: undefined,
    });
    expect(screen.getByRole("button", { name: "Abuse" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("explains an empty period", async () => {
    apiClient.listSafeguardEvents.mockResolvedValue([]);
    renderWithQueries(<SafeguardEvents />);

    expect(
      await screen.findByText("No Safeguard Events in this period"),
    ).toBeVisible();
  });

  it("offers Try again when events cannot be loaded", async () => {
    apiClient.listSafeguardEvents
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue([tom]);
    const user = userEvent.setup();
    renderWithQueries(<SafeguardEvents />);

    expect(
      await screen.findByText(
        "Safeguard itself is unaffected and still screening messages.",
      ),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Tom Hale")).toBeVisible();
  });
});
