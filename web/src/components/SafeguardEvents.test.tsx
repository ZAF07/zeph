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

    const table = within(await screen.findByRole("table"));
    const tomRow = within(table.getByText("Tom Hale").closest("tr")!);
    expect(tomRow.getByText("Suicide / self-harm")).toBeInTheDocument();
    expect(tomRow.getByText("Sent")).toBeInTheDocument();
    expect(tomRow.getByText("United Kingdom")).toBeInTheDocument();
    expect(tomRow.getByText(/10 Nov, \d\d:\d\d/)).toBeInTheDocument();
    const renRow = within(table.getByText("ren@example.com").closest("tr")!);
    expect(renRow.getByText("International fallback")).toBeInTheDocument();
    expect(table.getByText("No message content")).toBeInTheDocument();
    expect(tomRow.getByRole("link", { name: "Tom Hale" })).toHaveAttribute(
      "href",
      "/admin/users",
    );
    expect(apiClient.listSafeguardEvents).toHaveBeenCalledWith({
      riskType: undefined,
      days: 30,
    });
  });

  it("filters by risk type and period", async () => {
    const user = userEvent.setup();
    renderWithQueries(<SafeguardEvents />);
    await screen.findByRole("table");

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

  it("also shows each event as a card of label and value lines for phones", async () => {
    renderWithQueries(<SafeguardEvents />);
    await screen.findByRole("table");

    const lines = screen
      .getAllByRole("term")
      .map((term) => `${term.textContent}: ${term.nextSibling?.textContent}`);
    expect(lines.slice(0, 5)).toEqual([
      "User: Tom Hale",
      expect.stringMatching(/^Time: 10 Nov, \d\d:\d\d$/),
      "Risk type: Suicide / self-harm",
      "Crisis Reply: Sent",
      "Helplines shown: United Kingdom",
    ]);
  });

  it("says nothing matches when a risk type finds no events", async () => {
    const user = userEvent.setup();
    renderWithQueries(<SafeguardEvents />);
    await screen.findByRole("table");
    apiClient.listSafeguardEvents.mockResolvedValue([]);

    await user.click(screen.getByRole("button", { name: "Abuse" }));

    expect(
      await screen.findByText("Nothing matches these filters."),
    ).toBeVisible();
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

    expect(await screen.findByRole("table")).toBeInTheDocument();
  });
});
