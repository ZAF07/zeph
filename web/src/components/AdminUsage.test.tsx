import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminUsage } from "@/components/AdminUsage";
import type { ApiClient, UsageReport } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getUsage: vi.fn<ApiClient["getUsage"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const report: UsageReport = {
  rows: [
    {
      day: "2026-11-11",
      user_id: "u1",
      user_name: "Maya Lin",
      user_email: "maya@example.com",
      message_count: 24,
      tokens_in: 31240,
      tokens_out: 3880,
      web_search_count: 1,
      message_limit_reached: false,
      web_search_limit_reached: false,
    },
    {
      day: "2026-11-11",
      user_id: "u2",
      user_name: null,
      user_email: "ren@example.com",
      message_count: 60,
      tokens_in: 88910,
      tokens_out: 9402,
      web_search_count: 10,
      message_limit_reached: true,
      web_search_limit_reached: true,
    },
  ],
  daily_message_limit: 60,
  web_search_daily_limit: 10,
};

function readBlob(blob: Blob): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsText(blob);
  });
}

function totalValue(label: string) {
  return screen.getByText(label).nextElementSibling?.textContent;
}

function rowTexts() {
  const rows = within(screen.getByRole("table")).getAllByRole("row");
  return rows.slice(1).map((row) =>
    within(row)
      .getAllByRole("cell")
      .map((cell) => cell.textContent),
  );
}

describe("AdminUsage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getUsage.mockResolvedValue(report);
  });

  it("shows today's totals and usage per User per day, never message content", async () => {
    renderWithQueries(<AdminUsage />);

    expect(
      await screen.findByText(
        "No message content · daily limit 60 messages, 10 web searches",
      ),
    ).toBeInTheDocument();
    expect(apiClient.getUsage).toHaveBeenCalledWith(1);
    expect(totalValue("Tokens in · today")).toBe("120K");
    expect(totalValue("Tokens out · today")).toBe("13.3K");
    expect(totalValue("Messages · today")).toBe("84");
    expect(totalValue("Web searches · today")).toBe("11");
    expect(rowTexts()).toEqual([
      ["11 Nov", "Maya Lin", "24", "31,240", "3,880", "1", "—"],
      [
        "11 Nov",
        "ren@example.com",
        "60",
        "88,910",
        "9,402",
        "10",
        "Message limit reachedSearch limit reached",
      ],
    ]);
    expect(
      screen.getByText(
        "Tokens include Safeguard, response composition, post-conversation processing and Check-ins.",
      ),
    ).toBeVisible();
  });

  it("loads a longer period when picked", async () => {
    const user = userEvent.setup();
    renderWithQueries(<AdminUsage />);
    await screen.findByRole("table");

    await user.selectOptions(screen.getByLabelText("Period"), "Last 7 days");

    expect(apiClient.getUsage).toHaveBeenLastCalledWith(7);
    expect(
      await screen.findByText("Tokens in · last 7 days"),
    ).toBeInTheDocument();
  });

  it("downloads the rows as a CSV file", async () => {
    const user = userEvent.setup();
    const createObjectURL = vi.fn(() => "blob:usage");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
    renderWithQueries(<AdminUsage />);
    await screen.findByRole("table");

    await user.click(screen.getByRole("button", { name: "Download CSV" }));

    const [blob] = createObjectURL.mock.calls[0] as unknown as [Blob];
    expect(await readBlob(blob)).toContain(
      "2026-11-11,Maya Lin,maya@example.com,24,31240,3880,1",
    );
    expect(click).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:usage");
    vi.unstubAllGlobals();
    click.mockRestore();
  });

  it("says when there is no usage yet", async () => {
    apiClient.getUsage.mockResolvedValue({ ...report, rows: [] });
    renderWithQueries(<AdminUsage />);

    expect(await screen.findByText("No usage yet")).toBeVisible();
    expect(screen.getByRole("button", { name: "Download CSV" })).toBeDisabled();
  });

  it("offers to try again when usage can't be loaded", async () => {
    const user = userEvent.setup();
    apiClient.getUsage.mockRejectedValueOnce(new Error("down"));
    renderWithQueries(<AdminUsage />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("table")).toBeInTheDocument();
  });
});
