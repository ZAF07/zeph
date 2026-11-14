import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInKindsManager } from "@/components/CheckInKindsManager";
import {
  ApiError,
  type ApiClient,
  type CheckInKindOverview,
} from "@/lib/api-client";

const apiClient = {
  listCheckInKinds: vi.fn<ApiClient["listCheckInKinds"]>(),
  addCheckInKind: vi.fn<ApiClient["addCheckInKind"]>(),
  updateCheckInKind: vi.fn<ApiClient["updateCheckInKind"]>(),
  removeCheckInKind: vi.fn<ApiClient["removeCheckInKind"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const hello: CheckInKindOverview = {
  id: "kind-hello",
  name: "A casual hello",
  description: "Just checking how you are.",
  sends_shared_photo: false,
  sent_last_30_days: 12,
};

const followUp: CheckInKindOverview = {
  id: "kind-follow-up",
  name: "A follow-up",
  description: "On something you shared.",
  sends_shared_photo: false,
  sent_last_30_days: 1,
};

const lookBack: CheckInKindOverview = {
  id: "kind-look-back",
  name: "A look back at a photo",
  description: "One of the photos you shared.",
  sends_shared_photo: true,
  sent_last_30_days: 2,
};

async function findCard(name: string) {
  return within(await screen.findByRole("region", { name }));
}

describe("CheckInKindsManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listCheckInKinds.mockResolvedValue([hello, followUp]);
  });

  it("shows each Kind with its description and sends, with no memory switch", async () => {
    render(<CheckInKindsManager />);

    const card = await findCard("A casual hello");
    expect(card.getByLabelText("Name")).toHaveValue("A casual hello");
    expect(card.getByLabelText(/Description/)).toHaveValue(
      "Just checking how you are.",
    );
    expect(card.queryByRole("switch")).not.toBeInTheDocument();
    expect(card.queryByText(/memory/i)).not.toBeInTheDocument();
    expect(card.getByText("Sent 12 times in 30 days")).toBeInTheDocument();
    const followUpCard = await findCard("A follow-up");
    expect(followUpCard.queryByRole("switch")).not.toBeInTheDocument();
    expect(
      followUpCard.getByText("Sent 1 time in 30 days"),
    ).toBeInTheDocument();
  });

  it("says a Kind sends a Shared Photo and needs Photo Viewing", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([hello, lookBack]);
    render(<CheckInKindsManager />);

    const card = await findCard("A look back at a photo");
    expect(card.getByText("Sends a Shared Photo")).toBeInTheDocument();
    expect(
      card.getByText("Only for Users with Photo Viewing on and a Shared Photo"),
    ).toBeInTheDocument();
    expect(card.queryByText(/memory/i)).not.toBeInTheDocument();
    expect(card.getByRole("button", { name: "Remove" })).toBeInTheDocument();
    const helloCard = await findCard("A casual hello");
    expect(
      helloCard.queryByText("Sends a Shared Photo"),
    ).not.toBeInTheDocument();
  });

  it("saves an edited Kind", async () => {
    apiClient.updateCheckInKind.mockResolvedValue(hello);
    const user = userEvent.setup();
    render(<CheckInKindsManager />);
    const card = await findCard("A casual hello");
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.clear(card.getByLabelText(/Description/));
    await user.type(card.getByLabelText(/Description/), "A light hello.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateCheckInKind).toHaveBeenCalledWith("kind-hello", {
      name: "A casual hello",
      description: "A light hello.",
    });
    expect(
      await screen.findByText("Saved A casual hello."),
    ).toBeInTheDocument();
  });

  it("adds a new Kind", async () => {
    apiClient.addCheckInKind.mockResolvedValue({ ...hello, id: "new" });
    const user = userEvent.setup();
    render(<CheckInKindsManager />);
    await user.click(
      await screen.findByRole("button", { name: "Add Check-in Kind" }),
    );

    const card = await findCard("New Check-in Kind");
    await user.type(card.getByLabelText("Name"), "A gratitude nudge");
    await user.type(
      card.getByLabelText(/Description/),
      "One small good thing.",
    );
    await user.click(card.getByRole("button", { name: "Add" }));

    expect(apiClient.addCheckInKind).toHaveBeenCalledWith({
      name: "A gratitude nudge",
      description: "One small good thing.",
    });
    expect(
      await screen.findByText("Added A gratitude nudge."),
    ).toBeInTheDocument();
  });

  it("shows why the backend refused a Kind", async () => {
    apiClient.updateCheckInKind.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/check-in-kinds/kind-hello",
        "There is already a Check-in Kind called “A follow-up”.",
      ),
    );
    const user = userEvent.setup();
    render(<CheckInKindsManager />);
    const card = await findCard("A casual hello");

    await user.clear(card.getByLabelText("Name"));
    await user.type(card.getByLabelText("Name"), "A follow-up");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(await card.findByRole("alert")).toHaveTextContent(
      "There is already a Check-in Kind called “A follow-up”.",
    );
  });

  it("removes a Kind after confirming", async () => {
    apiClient.removeCheckInKind.mockResolvedValue();
    const user = userEvent.setup();
    render(<CheckInKindsManager />);
    const card = await findCard("A follow-up");

    await user.click(card.getByRole("button", { name: "Remove" }));
    expect(apiClient.removeCheckInKind).not.toHaveBeenCalled();
    apiClient.listCheckInKinds.mockResolvedValue([hello]);
    await user.click(card.getByRole("button", { name: "Remove A follow-up" }));

    expect(apiClient.removeCheckInKind).toHaveBeenCalledWith("kind-follow-up");
    expect(await screen.findByText("Removed A follow-up.")).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "A follow-up" }),
    ).not.toBeInTheDocument();
  });

  it("explains what happens with no Kinds", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([]);
    render(<CheckInKindsManager />);

    expect(await screen.findByText("No Check-in Kinds")).toBeInTheDocument();
  });

  it("offers Try again when the Kinds can't load", async () => {
    apiClient.listCheckInKinds.mockRejectedValue(new Error("down"));
    render(<CheckInKindsManager />);

    expect(
      await screen.findByText("Couldn’t load Check-in Kinds"),
    ).toBeInTheDocument();
  });
});
