import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NeedsManager } from "@/components/NeedsManager";
import { ApiError, type ApiClient, type Need } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listNeeds: vi.fn<ApiClient["listNeeds"]>(),
  addNeed: vi.fn<ApiClient["addNeed"]>(),
  updateNeed: vi.fn<ApiClient["updateNeed"]>(),
  deleteNeed: vi.fn<ApiClient["deleteNeed"]>(),
  moveNeed: vi.fn<ApiClient["moveNeed"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const beHeard: Need = {
  id: "need-be-heard",
  name: "Be heard",
  when_it_fits: "They are venting.",
  how_to_reply: "Listen and reflect back.",
  is_fallback: false,
};

const advice: Need = {
  id: "need-advice",
  name: "Advice",
  when_it_fits: "They ask what to do.",
  how_to_reply: "Give a real view.",
  is_fallback: false,
};

const askMore: Need = {
  id: "need-ask-more",
  name: "Ask more",
  when_it_fits: "It isn't clear.",
  how_to_reply: "Ask one short question.",
  is_fallback: true,
};

async function findCard(name: string) {
  return within(await screen.findByRole("region", { name }));
}

describe("NeedsManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listNeeds.mockResolvedValue([beHeard, advice, askMore]);
  });

  it("shows each Need in order with its name, when it fits and how to reply", async () => {
    renderWithQueries(<NeedsManager />);

    const card = await findCard("Be heard");
    expect(card.getByLabelText("Name")).toHaveValue("Be heard");
    expect(card.getByLabelText(/When it fits/)).toHaveValue(
      "They are venting.",
    );
    expect(card.getByLabelText(/How to reply/)).toHaveValue(
      "Listen and reflect back.",
    );
    expect(
      screen
        .getAllByRole("region")
        .map((region) => region.getAttribute("aria-label")),
    ).toEqual(["Be heard", "Advice", "Ask more"]);
  });

  it("marks the fallback Need and offers no Remove for it", async () => {
    renderWithQueries(<NeedsManager />);

    const card = await findCard("Ask more");
    expect(card.getByText("Fallback · can’t be deleted")).toBeInTheDocument();
    expect(
      card.queryByRole("button", { name: "Remove" }),
    ).not.toBeInTheDocument();
    const adviceCard = await findCard("Advice");
    expect(
      adviceCard.getByRole("button", { name: "Remove" }),
    ).toBeInTheDocument();
  });

  it("saves an edited Need", async () => {
    apiClient.updateNeed.mockResolvedValue(advice);
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    const card = await findCard("Advice");
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.clear(card.getByLabelText(/How to reply/));
    await user.type(card.getByLabelText(/How to reply/), "One idea only.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateNeed).toHaveBeenCalledWith("need-advice", {
      name: "Advice",
      when_it_fits: "They ask what to do.",
      how_to_reply: "One idea only.",
    });
    expect(await screen.findByText("Saved Advice.")).toBeInTheDocument();
  });

  it("adds a new Need", async () => {
    apiClient.addNeed.mockResolvedValue({ ...advice, id: "new" });
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    await user.click(await screen.findByRole("button", { name: "Add Need" }));

    const card = await findCard("New Need");
    await user.type(card.getByLabelText("Name"), "Celebrate");
    await user.type(card.getByLabelText(/When it fits/), "Good news.");
    await user.type(card.getByLabelText(/How to reply/), "Cheer them on.");
    await user.click(card.getByRole("button", { name: "Add" }));

    expect(apiClient.addNeed).toHaveBeenCalledWith({
      name: "Celebrate",
      when_it_fits: "Good news.",
      how_to_reply: "Cheer them on.",
    });
    expect(await screen.findByText("Added Celebrate.")).toBeInTheDocument();
  });

  it("shows why the backend refused a Need", async () => {
    apiClient.updateNeed.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/needs/need-advice",
        "There is already a Need called “be heard”.",
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    const card = await findCard("Advice");

    await user.clear(card.getByLabelText("Name"));
    await user.type(card.getByLabelText("Name"), "be heard");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(await card.findByRole("alert")).toHaveTextContent(
      "There is already a Need called “be heard”.",
    );
  });

  it("removes a Need after confirming", async () => {
    apiClient.deleteNeed.mockResolvedValue();
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    const card = await findCard("Advice");

    await user.click(card.getByRole("button", { name: "Remove" }));
    expect(apiClient.deleteNeed).not.toHaveBeenCalled();
    apiClient.listNeeds.mockResolvedValue([beHeard, askMore]);
    await user.click(card.getByRole("button", { name: "Remove Advice" }));

    expect(apiClient.deleteNeed).toHaveBeenCalledWith("need-advice");
    expect(await screen.findByText("Removed Advice.")).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Advice" }),
    ).not.toBeInTheDocument();
  });

  it("moves a Need up and shows the new order", async () => {
    apiClient.moveNeed.mockResolvedValue([advice, beHeard, askMore]);
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    const card = await findCard("Advice");

    apiClient.listNeeds.mockResolvedValue([advice, beHeard, askMore]);
    await user.click(card.getByRole("button", { name: "Move Advice up" }));

    expect(apiClient.moveNeed).toHaveBeenCalledWith("need-advice", "up");
    await vi.waitFor(() =>
      expect(
        screen
          .getAllByRole("region")
          .map((region) => region.getAttribute("aria-label")),
      ).toEqual(["Advice", "Be heard", "Ask more"]),
    );
  });

  it("can't move the first Need up or the last one down", async () => {
    renderWithQueries(<NeedsManager />);

    const first = await findCard("Be heard");
    expect(
      first.getByRole("button", { name: "Move Be heard up" }),
    ).toBeDisabled();
    const last = await findCard("Ask more");
    expect(
      last.getByRole("button", { name: "Move Ask more down" }),
    ).toBeDisabled();
  });

  it("says so when a move fails", async () => {
    apiClient.moveNeed.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<NeedsManager />);
    const card = await findCard("Advice");

    await user.click(card.getByRole("button", { name: "Move Advice down" }));

    expect(
      await screen.findByText("Couldn’t move Advice. Please try again."),
    ).toBeInTheDocument();
  });

  it("offers Try again when the Needs can't load", async () => {
    apiClient.listNeeds.mockRejectedValue(new Error("down"));
    renderWithQueries(<NeedsManager />);

    expect(await screen.findByText("Couldn’t load Needs")).toBeInTheDocument();
  });
});
