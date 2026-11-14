import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { HelplinesManager } from "@/components/HelplinesManager";
import {
  ApiError,
  type ApiClient,
  type Helpline,
  type Helplines,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listHelplines: vi.fn<ApiClient["listHelplines"]>(),
  addHelpline: vi.fn<ApiClient["addHelpline"]>(),
  updateHelpline: vi.fn<ApiClient["updateHelpline"]>(),
  deleteHelpline: vi.fn<ApiClient["deleteHelpline"]>(),
  moveHelpline: vi.fn<ApiClient["moveHelpline"]>(),
  updateInternationalFallback:
    vi.fn<ApiClient["updateInternationalFallback"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function helpline(
  id: string,
  country: string | null,
  name: string,
  number: string,
  sortOrder: number,
): Helpline {
  return {
    id,
    country,
    name,
    number,
    hours: "24 hours",
    sort_order: sortOrder,
  };
}

const sos = helpline("sos", "SG", "Samaritans of Singapore (SOS)", "1767", 0);
const imh = helpline("imh", "SG", "IMH Mental Health Helpline", "6389 2222", 1);
const samaritans = helpline("uk", "GB", "Samaritans", "116 123", 0);
const fallback: Helpline = {
  id: "fallback",
  country: null,
  name: "Find A Helpline",
  number: "findahelpline.com",
  hours: null,
  sort_order: 0,
};

const seeded: Helplines = {
  helplines: [samaritans, sos, imh],
  international_fallback: fallback,
};

function rowFor(name: string): HTMLElement {
  const row = screen.getByText(name).closest("tr");
  if (!row) {
    throw new Error(`No row for ${name}`);
  }
  return row;
}

describe("HelplinesManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listHelplines.mockResolvedValue(seeded);
  });

  it("lists every country's Helplines with the fallback last", async () => {
    renderWithQueries(<HelplinesManager />);

    await screen.findByText("Samaritans of Singapore (SOS)");
    const sosRow = within(rowFor("Samaritans of Singapore (SOS)"));
    expect(sosRow.getByText("Singapore")).toBeInTheDocument();
    expect(sosRow.getByText("1767")).toBeInTheDocument();
    expect(sosRow.getByText("24 hours")).toBeInTheDocument();
    const rows = screen.getAllByRole("row");
    expect(rows.at(-1)).toHaveTextContent("International fallback");
    expect(rows.at(-1)).toHaveTextContent("findahelpline.com");
    expect(
      within(rowFor("International fallback")).queryByRole("button", {
        name: /Remove/,
      }),
    ).toBeNull();
  });

  it("filters by country", async () => {
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    await user.selectOptions(screen.getByLabelText("Country"), "Singapore");

    expect(screen.queryByText("Samaritans")).toBeNull();
    expect(screen.getByText("IMH Mental Health Helpline")).toBeVisible();
  });

  it("adds a Helpline", async () => {
    apiClient.addHelpline.mockResolvedValue(
      helpline("chat", "SG", "CHAT", "6493 6500", 2),
    );
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    await user.click(screen.getByRole("button", { name: "Add Helpline" }));
    const form = within(screen.getByRole("form", { name: "Add Helpline" }));
    await user.selectOptions(form.getByLabelText("Country"), "Singapore");
    await user.type(form.getByLabelText("Name"), "CHAT");
    await user.type(form.getByLabelText("Number"), "6493 6500");
    await user.click(form.getByRole("button", { name: "Add Helpline" }));

    expect(apiClient.addHelpline).toHaveBeenCalledWith({
      country: "SG",
      name: "CHAT",
      number: "6493 6500",
      hours: null,
    });
    expect(await screen.findByText("Added CHAT.")).toBeVisible();
    expect(screen.queryByRole("form")).toBeNull();
    expect(apiClient.listHelplines).toHaveBeenCalledTimes(2);
  });

  it("edits a Helpline", async () => {
    apiClient.updateHelpline.mockResolvedValue({ ...imh, hours: "Mon–Fri" });
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("IMH Mental Health Helpline");

    await user.click(
      within(rowFor("IMH Mental Health Helpline")).getByRole("button", {
        name: "Edit",
      }),
    );
    const form = within(
      screen.getByRole("form", { name: "Edit IMH Mental Health Helpline" }),
    );
    const hours = form.getByLabelText("Hours");
    await user.clear(hours);
    await user.type(hours, "Mon–Fri");
    await user.click(form.getByRole("button", { name: "Save" }));

    expect(apiClient.updateHelpline).toHaveBeenCalledWith("imh", {
      country: "SG",
      name: "IMH Mental Health Helpline",
      number: "6389 2222",
      hours: "Mon–Fri",
    });
  });

  it("shows why the backend refused a Helpline", async () => {
    apiClient.updateHelpline.mockRejectedValue(
      new ApiError(422, "/api/admin/helplines/imh", "A Helpline needs a name."),
    );
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("IMH Mental Health Helpline");

    await user.click(
      within(rowFor("IMH Mental Health Helpline")).getByRole("button", {
        name: "Edit",
      }),
    );
    const form = within(screen.getByRole("form"));
    await user.type(form.getByLabelText("Name"), " (IMH)");
    await user.click(form.getByRole("button", { name: "Save" }));

    expect(await form.findByRole("alert")).toHaveTextContent(
      "A Helpline needs a name.",
    );
  });

  it("edits the international fallback without a country", async () => {
    apiClient.updateInternationalFallback.mockResolvedValue(fallback);
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Find A Helpline");

    await user.click(
      screen.getByRole("button", { name: "Edit international fallback" }),
    );
    const form = within(
      screen.getByRole("form", { name: "Edit international fallback" }),
    );
    expect(form.queryByLabelText("Country")).toBeNull();
    await user.clear(form.getByLabelText("Name"));
    await user.type(form.getByLabelText("Name"), "IASP");
    await user.click(form.getByRole("button", { name: "Save" }));

    expect(apiClient.updateInternationalFallback).toHaveBeenCalledWith({
      name: "IASP",
      number: "findahelpline.com",
      hours: null,
    });
  });

  it("removes a Helpline after confirming", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    apiClient.deleteHelpline.mockResolvedValue();
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    await user.click(screen.getByRole("button", { name: "Remove Samaritans" }));

    expect(window.confirm).toHaveBeenCalledWith("Remove Samaritans?");
    expect(apiClient.deleteHelpline).toHaveBeenCalledWith("uk");
    expect(await screen.findByText("Removed Samaritans.")).toBeVisible();
  });

  it("keeps a Helpline when removing is not confirmed", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    await user.click(screen.getByRole("button", { name: "Remove Samaritans" }));

    expect(apiClient.deleteHelpline).not.toHaveBeenCalled();
  });

  it("moves a Helpline within its country, but not past the ends", async () => {
    apiClient.moveHelpline.mockResolvedValue([imh, sos]);
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    expect(
      screen.getByRole("button", {
        name: "Move Samaritans of Singapore (SOS) up",
      }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", {
        name: "Move IMH Mental Health Helpline down",
      }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move Samaritans up" }),
    ).toBeDisabled();
    await user.click(
      screen.getByRole("button", {
        name: "Move IMH Mental Health Helpline up",
      }),
    );

    expect(apiClient.moveHelpline).toHaveBeenCalledWith("imh", "up");
  });

  it("says so when a row change fails", async () => {
    apiClient.moveHelpline.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);
    await screen.findByText("Samaritans");

    await user.click(
      screen.getByRole("button", {
        name: "Move IMH Mental Health Helpline up",
      }),
    );

    expect(
      await screen.findByText(
        "Couldn’t change IMH Mental Health Helpline. Please try again.",
      ),
    ).toBeVisible();
  });

  it("explains the fallback when there are no country Helplines", async () => {
    apiClient.listHelplines.mockResolvedValue({
      helplines: [],
      international_fallback: fallback,
    });
    renderWithQueries(<HelplinesManager />);

    expect(await screen.findByText("No Helplines yet")).toBeVisible();
    expect(screen.getByText("Find A Helpline")).toBeVisible();
  });

  it("offers Try again when Helplines cannot be loaded", async () => {
    apiClient.listHelplines
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(seeded);
    const user = userEvent.setup();
    renderWithQueries(<HelplinesManager />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Samaritans")).toBeVisible();
  });
});
