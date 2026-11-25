import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CheckInKindsManager } from "@/components/CheckInKindsManager";
import {
  ApiError,
  type ApiClient,
  type CheckInKindOverview,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

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
  raises_curiosity: false,
  shares_pattern: false,
  sent_last_30_days: 12,
};

const followUp: CheckInKindOverview = {
  id: "kind-follow-up",
  name: "A follow-up",
  description: "On something you shared.",
  sends_shared_photo: false,
  raises_curiosity: false,
  shares_pattern: false,
  sent_last_30_days: 1,
};

const lookBack: CheckInKindOverview = {
  id: "kind-look-back",
  name: "A look back at a photo",
  description: "One of the photos you shared.",
  sends_shared_photo: true,
  raises_curiosity: false,
  shares_pattern: false,
  sent_last_30_days: 2,
};

const wondering: CheckInKindOverview = {
  id: "kind-wondering",
  name: "Something I've been wondering",
  description: "A question about something you mentioned.",
  sends_shared_photo: false,
  raises_curiosity: true,
  shares_pattern: false,
  sent_last_30_days: 3,
};

async function findCard(name: string) {
  return within(await screen.findByRole("region", { name }));
}

async function findCardToggle(name: string) {
  const card = await findCard(name);
  return card.getByRole("button", { name: new RegExp(`^${name}`) });
}

describe("CheckInKindsManager", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listCheckInKinds.mockResolvedValue([hello, followUp]);
  });

  it("shows each Kind's name, description and sends on its row, with no memory switch", async () => {
    renderWithQueries(<CheckInKindsManager />);

    const card = await findCard("A casual hello");
    expect(screen.getByText("kinds", { exact: false })).toHaveTextContent(
      "2 kinds",
    );
    expect(card.getByLabelText("Name")).toHaveValue("A casual hello");
    expect(card.getByLabelText("Description")).toHaveValue(
      "Just checking how you are.",
    );
    expect(card.queryByRole("switch")).not.toBeInTheDocument();
    expect(card.queryByText(/memory/i)).not.toBeInTheDocument();
    expect(await findCardToggle("A casual hello")).toHaveTextContent(
      "12 sent in 30 days",
    );
    expect(await findCardToggle("A follow-up")).toHaveTextContent(
      "A follow-upOn something you shared.1 sent in 30 days",
    );
  });

  it("opens the first card and folds the rest", async () => {
    renderWithQueries(<CheckInKindsManager />);

    expect(await findCardToggle("A casual hello")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(await findCardToggle("A follow-up")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    const followUpCard = await findCard("A follow-up");
    expect(followUpCard.getByLabelText("Name")).not.toBeVisible();
  });

  it("opens and folds a card from anywhere on its top row", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const followUpCard = await findCard("A follow-up");
    const toggle = within(await findCardToggle("A follow-up"));

    await user.click(toggle.getByText("On something you shared."));
    expect(await findCardToggle("A follow-up")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(followUpCard.getByLabelText("Name")).toBeVisible();

    await user.click(toggle.getByText("sent in 30 days", { exact: false }));
    expect(await findCardToggle("A follow-up")).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(followUpCard.getByLabelText("Name")).not.toBeVisible();
  });

  it("keeps several cards open at once", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);

    await user.click(await findCardToggle("A follow-up"));

    expect(await findCardToggle("A casual hello")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(await findCardToggle("A follow-up")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("opens every card with Expand all and folds them with Collapse all", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    await findCard("A casual hello");

    await user.click(screen.getByRole("button", { name: "Expand all" }));
    for (const name of ["A casual hello", "A follow-up"]) {
      expect(await findCardToggle(name)).toHaveAttribute(
        "aria-expanded",
        "true",
      );
    }

    await user.click(screen.getByRole("button", { name: "Collapse all" }));
    for (const name of ["A casual hello", "A follow-up"]) {
      expect(await findCardToggle(name)).toHaveAttribute(
        "aria-expanded",
        "false",
      );
    }
  });

  it("marks a folded card with unsaved edits and keeps its text", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");
    const toggle = await findCardToggle("A casual hello");
    expect(card.queryByText("Unsaved changes")).not.toBeInTheDocument();

    await user.type(card.getByLabelText("Description"), " Today.");
    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(within(toggle).getByText("Unsaved changes")).toBeVisible();
    await user.click(toggle);
    expect(card.getByLabelText("Description")).toHaveValue(
      "Just checking how you are. Today.",
    );
  });

  it("puts back the saved text with Discard", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");
    expect(card.getByRole("button", { name: "Discard" })).toBeDisabled();

    await user.type(card.getByLabelText("Name"), "!");
    await user.click(card.getByRole("button", { name: "Discard" }));

    expect(card.getByLabelText("Name")).toHaveValue("A casual hello");
    expect(card.queryByText("Unsaved changes")).not.toBeInTheDocument();
  });

  it("tags a Kind that sends a Shared Photo", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([hello, lookBack]);
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);

    const toggle = await findCardToggle("A look back at a photo");
    expect(toggle).toHaveTextContent("Sends a Shared Photo");
    await user.click(toggle);
    const card = await findCard("A look back at a photo");
    expect(card.queryByText(/memory/i)).not.toBeInTheDocument();
    expect(card.getByRole("button", { name: "Remove" })).toBeInTheDocument();
    expect(await findCardToggle("A casual hello")).not.toHaveTextContent(
      "Sends a Shared Photo",
    );
  });

  it("tags a Kind that asks a Curiosity", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([hello, wondering]);
    renderWithQueries(<CheckInKindsManager />);

    const toggle = await findCardToggle("Something I've been wondering");
    expect(toggle).toHaveTextContent("Asks a Curiosity");
    expect(toggle).not.toHaveTextContent("Sends a Shared Photo");
    expect(await findCardToggle("A casual hello")).not.toHaveTextContent(
      "Asks a Curiosity",
    );
  });

  it("tags a Kind that shares a Pattern", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([
      hello,
      {
        ...hello,
        id: "kind-noticed",
        name: "Something I've noticed",
        shares_pattern: true,
      },
    ]);
    renderWithQueries(<CheckInKindsManager />);

    expect(await findCardToggle("Something I've noticed")).toHaveTextContent(
      "Shares a Pattern",
    );
    expect(await findCardToggle("A casual hello")).not.toHaveTextContent(
      "Shares a Pattern",
    );
  });

  it("saves an edited Kind", async () => {
    apiClient.updateCheckInKind.mockResolvedValue(hello);
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.clear(card.getByLabelText("Description"));
    await user.type(card.getByLabelText("Description"), "A light hello.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateCheckInKind).toHaveBeenCalledWith("kind-hello", {
      name: "A casual hello",
      description: "A light hello.",
    });
    expect(
      await screen.findByText("Saved A casual hello."),
    ).toBeInTheDocument();
  });

  it("adds a new Kind above the list", async () => {
    apiClient.addCheckInKind.mockResolvedValue({ ...hello, id: "new" });
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    await user.click(
      await screen.findByRole("button", { name: "Add a Check-in Kind" }),
    );

    const card = await findCard("New Check-in Kind");
    expect(card.getByText("Not saved yet")).toBeInTheDocument();
    expect(card.getByRole("button", { name: "Add" })).toBeDisabled();
    await user.type(card.getByLabelText("Name"), "A gratitude nudge");
    await user.type(
      card.getByLabelText("Description"),
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

  it("shows why the backend refused a Kind in the save bar", async () => {
    apiClient.updateCheckInKind.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/check-in-kinds/kind-hello",
        "There is already a Check-in Kind called “A follow-up”.",
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");

    await user.clear(card.getByLabelText("Name"));
    await user.type(card.getByLabelText("Name"), "A follow-up");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(await card.findByRole("alert")).toHaveTextContent(
      "There is already a Check-in Kind called “A follow-up”.",
    );
    expect(card.getByLabelText("Name")).toHaveValue("A follow-up");
  });

  it("says a save failed and keeps the text", async () => {
    apiClient.updateCheckInKind.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");

    await user.type(card.getByLabelText("Name"), "!");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(await card.findByRole("alert")).toHaveTextContent(
      "Couldn’t save the Check-in Kind. Please try again.",
    );
    expect(card.getByLabelText("Name")).toHaveValue("A casual hello!");
  });

  it("removes a Kind after confirming inside its card", async () => {
    apiClient.removeCheckInKind.mockResolvedValue();
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A follow-up");
    await user.click(await findCardToggle("A follow-up"));

    await user.click(card.getByRole("button", { name: "Remove" }));
    const confirm = card.getByRole("alertdialog", {
      name: "Remove this kind?",
    });
    expect(confirm).toHaveTextContent("Remove “A follow-up”?");
    expect(apiClient.removeCheckInKind).not.toHaveBeenCalled();
    apiClient.listCheckInKinds.mockResolvedValue([hello]);
    await user.click(within(confirm).getByRole("button", { name: "Remove" }));

    expect(apiClient.removeCheckInKind).toHaveBeenCalledWith("kind-follow-up");
    expect(await screen.findByText("Removed A follow-up.")).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "A follow-up" }),
    ).not.toBeInTheDocument();
  });

  it("says a remove failed in the save bar", async () => {
    apiClient.removeCheckInKind.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");

    await user.click(card.getByRole("button", { name: "Remove" }));
    await user.click(
      within(card.getByRole("alertdialog")).getByRole("button", {
        name: "Remove",
      }),
    );

    expect(await card.findByRole("alert")).toHaveTextContent(
      "Couldn’t remove the Check-in Kind. Please try again.",
    );
    expect(card.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("keeps a Kind when Keep it is chosen", async () => {
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);
    const card = await findCard("A casual hello");

    await user.click(card.getByRole("button", { name: "Remove" }));
    await user.click(card.getByRole("button", { name: "Keep it" }));

    expect(card.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(apiClient.removeCheckInKind).not.toHaveBeenCalled();
  });

  it("explains what happens with no Kinds and offers to add one", async () => {
    apiClient.listCheckInKinds.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<CheckInKindsManager />);

    expect(await screen.findByText("No Check-in Kinds")).toBeInTheDocument();
    const addButtons = screen.getAllByRole("button", {
      name: "Add a Check-in Kind",
    });
    await user.click(addButtons[addButtons.length - 1]);
    expect(await findCard("New Check-in Kind")).toBeTruthy();
  });

  it("shows a loading list while the Kinds load", () => {
    apiClient.listCheckInKinds.mockReturnValue(new Promise(() => {}));
    renderWithQueries(<CheckInKindsManager />);

    expect(
      screen.getByRole("status", { name: "Loading Check-in Kinds" }),
    ).toBeInTheDocument();
  });

  it("offers Try again when the Kinds can't load", async () => {
    apiClient.listCheckInKinds.mockRejectedValue(new Error("down"));
    renderWithQueries(<CheckInKindsManager />);

    expect(
      await screen.findByText("Couldn’t load Check-in Kinds"),
    ).toBeInTheDocument();
  });
});
