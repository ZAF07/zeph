import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MovesManager } from "@/components/MovesManager";
import {
  ApiError,
  type ApiClient,
  type FeatureSwitch,
  type Move,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listMoves: vi.fn<ApiClient["listMoves"]>(),
  addMove: vi.fn<ApiClient["addMove"]>(),
  updateMove: vi.fn<ApiClient["updateMove"]>(),
  deleteMove: vi.fn<ApiClient["deleteMove"]>(),
  moveMove: vi.fn<ApiClient["moveMove"]>(),
  listFeatures: vi.fn<ApiClient["listFeatures"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const calm: Move = {
  id: "move-calm",
  name: "Calm",
  when_it_fits: "They are anxious.",
  how_to_do_it: "Slow things down.",
  needed_feature: null,
  asks_a_question: false,
};

const push: Move = {
  id: "move-push",
  name: "Push",
  when_it_fits: "They are stalling.",
  how_to_do_it: "Name the gap kindly.",
  needed_feature: null,
  asks_a_question: false,
};

const research: Move = {
  id: "move-research",
  name: "Research",
  when_it_fits: "They need options found.",
  how_to_do_it: "Look up real options.",
  needed_feature: "web_search",
  asks_a_question: false,
};

const webSearch: FeatureSwitch = {
  feature: "web_search",
  name: "Web Search",
  description: "Zeph can look things up.",
  on: true,
  changed_by_email: null,
  changed_at: null,
};

const stickers: FeatureSwitch = {
  ...webSearch,
  feature: "stickers",
  name: "Stickers",
};

async function findCard(name: string) {
  return within(await screen.findByRole("region", { name }));
}

describe("MovesManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listMoves.mockResolvedValue([calm, push, research]);
    apiClient.listFeatures.mockResolvedValue([webSearch, stickers]);
  });

  it("shows each Move in order with its text and the Feature it needs", async () => {
    renderWithQueries(<MovesManager />);

    const card = await findCard("Research");
    expect(card.getByLabelText("Name")).toHaveValue("Research");
    expect(card.getByLabelText(/When it fits/)).toHaveValue(
      "They need options found.",
    );
    expect(card.getByLabelText(/How to do it/)).toHaveValue(
      "Look up real options.",
    );
    expect(
      await card.findByRole("option", { name: "Web Search" }),
    ).toBeInTheDocument();
    expect(card.getByLabelText(/Needs a Feature/)).toHaveValue("web_search");
    expect(
      (await findCard("Calm")).getByLabelText(/Needs a Feature/),
    ).toHaveValue("");
    expect(
      screen
        .getAllByRole("region")
        .map((region) => region.getAttribute("aria-label")),
    ).toEqual(["Calm", "Push", "Research"]);
  });

  it("saves an edited Move with the Feature it needs", async () => {
    apiClient.updateMove.mockResolvedValue(push);
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Push");
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();
    await card.findByRole("option", { name: "Stickers" });

    await user.clear(card.getByLabelText(/How to do it/));
    await user.type(card.getByLabelText(/How to do it/), "Ask for one step.");
    await user.selectOptions(
      card.getByLabelText(/Needs a Feature/),
      "stickers",
    );
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateMove).toHaveBeenCalledWith("move-push", {
      name: "Push",
      when_it_fits: "They are stalling.",
      how_to_do_it: "Ask for one step.",
      needed_feature: "stickers",
      asks_a_question: false,
    });
    expect(await screen.findByText("Saved Push.")).toBeInTheDocument();
  });

  it("shows whether each Move asks a question", async () => {
    apiClient.listMoves.mockResolvedValue([
      calm,
      { ...push, asks_a_question: true },
    ]);
    renderWithQueries(<MovesManager />);

    expect(
      (await findCard("Push")).getByRole("checkbox", {
        name: /Asks a question/,
      }),
    ).toBeChecked();
    expect(
      (await findCard("Calm")).getByRole("checkbox", {
        name: /Asks a question/,
      }),
    ).not.toBeChecked();
  });

  it("saves a Move with Asks a question ticked", async () => {
    apiClient.updateMove.mockResolvedValue({ ...calm, asks_a_question: true });
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Calm");

    await user.click(card.getByRole("checkbox", { name: /Asks a question/ }));
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateMove).toHaveBeenCalledWith("move-calm", {
      name: "Calm",
      when_it_fits: "They are anxious.",
      how_to_do_it: "Slow things down.",
      needed_feature: null,
      asks_a_question: true,
    });
    expect(await screen.findByText("Saved Calm.")).toBeInTheDocument();
  });

  it("adds a new Move that needs no Feature", async () => {
    apiClient.addMove.mockResolvedValue({ ...calm, id: "new" });
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    await user.click(await screen.findByRole("button", { name: "Add Move" }));

    const card = await findCard("New Move");
    await user.type(card.getByLabelText("Name"), "Celebrate");
    await user.type(card.getByLabelText(/When it fits/), "Good news.");
    await user.type(card.getByLabelText(/How to do it/), "Cheer them on.");
    await user.click(card.getByRole("button", { name: "Add" }));

    expect(apiClient.addMove).toHaveBeenCalledWith({
      name: "Celebrate",
      when_it_fits: "Good news.",
      how_to_do_it: "Cheer them on.",
      needed_feature: null,
      asks_a_question: false,
    });
    expect(await screen.findByText("Added Celebrate.")).toBeInTheDocument();
  });

  it("shows why the backend refused a Move with a taken name", async () => {
    apiClient.updateMove.mockRejectedValue(
      new ApiError(
        409,
        "/api/admin/moves/move-push",
        "There is already a Move called “calm”.",
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Push");

    await user.clear(card.getByLabelText("Name"));
    await user.type(card.getByLabelText("Name"), "calm");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(await card.findByRole("alert")).toHaveTextContent(
      "There is already a Move called “calm”.",
    );
  });

  it("removes a Move after confirming", async () => {
    apiClient.deleteMove.mockResolvedValue();
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Push");

    await user.click(card.getByRole("button", { name: "Remove" }));
    expect(apiClient.deleteMove).not.toHaveBeenCalled();
    apiClient.listMoves.mockResolvedValue([calm, research]);
    await user.click(card.getByRole("button", { name: "Remove Push" }));

    expect(apiClient.deleteMove).toHaveBeenCalledWith("move-push");
    expect(await screen.findByText("Removed Push.")).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Push" }),
    ).not.toBeInTheDocument();
  });

  it("moves a Move up and shows the new order", async () => {
    apiClient.moveMove.mockResolvedValue([push, calm, research]);
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Push");

    apiClient.listMoves.mockResolvedValue([push, calm, research]);
    await user.click(card.getByRole("button", { name: "Move Push up" }));

    expect(apiClient.moveMove).toHaveBeenCalledWith("move-push", "up");
    await vi.waitFor(() =>
      expect(
        screen
          .getAllByRole("region")
          .map((region) => region.getAttribute("aria-label")),
      ).toEqual(["Push", "Calm", "Research"]),
    );
  });

  it("can't move the first Move up or the last one down", async () => {
    renderWithQueries(<MovesManager />);

    const first = await findCard("Calm");
    expect(first.getByRole("button", { name: "Move Calm up" })).toBeDisabled();
    const last = await findCard("Research");
    expect(
      last.getByRole("button", { name: "Move Research down" }),
    ).toBeDisabled();
  });

  it("says so when a move fails", async () => {
    apiClient.moveMove.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<MovesManager />);
    const card = await findCard("Push");

    await user.click(card.getByRole("button", { name: "Move Push down" }));

    expect(
      await screen.findByText("Couldn’t move Push. Please try again."),
    ).toBeInTheDocument();
  });

  it("offers Try again when the Moves can't load", async () => {
    apiClient.listMoves.mockRejectedValue(new Error("down"));
    renderWithQueries(<MovesManager />);

    expect(await screen.findByText("Couldn’t load Moves")).toBeInTheDocument();
  });
});
