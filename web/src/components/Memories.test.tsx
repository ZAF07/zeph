import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Memories } from "@/components/Memories";
import type {
  ApiClient,
  ConversationSummary,
  MemoryGroup,
} from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
  listMemoryGroups: vi.fn<ApiClient["listMemoryGroups"]>(),
  deleteMemoryItem: vi.fn<ApiClient["deleteMemoryItem"]>(),
  deleteAllMemoryItems: vi.fn<ApiClient["deleteAllMemoryItems"]>(),
  listConversationSummaries: vi.fn<ApiClient["listConversationSummaries"]>(),
  deleteConversationSummary: vi.fn<ApiClient["deleteConversationSummary"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const maya = { ...userWithRole("user"), time_zone: "UTC" };

const groups: MemoryGroup[] = [
  {
    category: "Life details",
    items: [
      {
        id: "item-1",
        content: "Started a new role in product design",
        source: "conversation",
        created_at: "2026-10-02T09:00:00Z",
        updated_at: "2026-10-02T09:00:00Z",
      },
      {
        id: "item-2",
        content: "Goes by Maya",
        source: "onboarding",
        created_at: "2026-09-30T09:00:00Z",
        updated_at: "2026-09-30T09:00:00Z",
      },
    ],
  },
  {
    category: "What helps",
    items: [
      {
        id: "item-3",
        content: "Walking helps when thoughts spiral",
        source: "conversation",
        created_at: "2026-10-15T09:00:00Z",
        updated_at: "2026-10-15T09:00:00Z",
      },
    ],
  },
];

const summaries: ConversationSummary[] = [
  {
    id: "summary-1",
    summary: "Talked through whether to accept the new role.",
    mood: "unsettled at first, then calmer",
    created_at: "2026-11-11T09:00:00Z",
  },
  {
    id: "summary-2",
    summary: "A short Conversation after a morning swim.",
    mood: "light and content",
    created_at: "2026-11-09T09:00:00Z",
  },
];

describe("Memories", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(maya);
    apiClient.listMemoryGroups.mockResolvedValue(groups);
    apiClient.listConversationSummaries.mockResolvedValue(summaries);
    apiClient.deleteMemoryItem.mockResolvedValue(undefined);
    apiClient.deleteAllMemoryItems.mockResolvedValue(undefined);
    apiClient.deleteConversationSummary.mockResolvedValue(undefined);
  });

  it("marks User Memory as changed in chat with the day", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      changed_in_chat: { user_memory: "2026-11-03T09:00:00Z" },
    });
    render(<Memories />);

    expect(
      await screen.findByText("Changed in chat · 3 Nov"),
    ).toBeInTheDocument();
  });

  it("shows Memory Items grouped by Memory Category with where they came from", async () => {
    render(<Memories />);

    const lifeDetails = within(
      await screen.findByRole("region", { name: "Life details" }),
    );
    expect(
      lifeDetails.getByText("Started a new role in product design"),
    ).toBeVisible();
    expect(lifeDetails.getByText("From a conversation · 2 Oct")).toBeVisible();
    expect(lifeDetails.getByText("From onboarding · 30 Sept")).toBeVisible();
    expect(
      screen.getByRole("region", { name: "What helps" }),
    ).toBeInTheDocument();
    expect(screen.getByText("3 memories, grouped by category")).toBeVisible();
  });

  it("deletes a single Memory Item", async () => {
    const user = userEvent.setup();
    render(<Memories />);

    await user.click(
      await screen.findByRole("button", {
        name: "Delete memory: Walking helps when thoughts spiral",
      }),
    );

    expect(apiClient.deleteMemoryItem).toHaveBeenCalledWith("item-3");
    expect(
      screen.queryByText("Walking helps when thoughts spiral"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "What helps" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("2 memories, grouped by category")).toBeVisible();
  });

  it("keeps a Memory Item and explains when deleting it fails", async () => {
    apiClient.deleteMemoryItem.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<Memories />);

    await user.click(
      await screen.findByRole("button", {
        name: "Delete memory: Goes by Maya",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(screen.getByText("Goes by Maya")).toBeVisible();
  });

  it("deletes all Memory Items only after confirming", async () => {
    const user = userEvent.setup();
    render(<Memories />);

    await user.click(
      await screen.findByRole("button", { name: "Delete all memories" }),
    );
    expect(screen.getByText("Delete all 3 memories?")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Keep them" }));
    expect(apiClient.deleteAllMemoryItems).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: "Delete all memories" }),
    );
    await user.click(screen.getByRole("button", { name: "Yes, delete all" }));

    expect(apiClient.deleteAllMemoryItems).toHaveBeenCalledOnce();
    expect(
      await screen.findByText("Zeph hasn’t remembered anything yet"),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Delete all memories" }),
    ).not.toBeInTheDocument();
  });

  it("lists Conversation Summaries by date with how the User seemed", async () => {
    const user = userEvent.setup();
    render(<Memories />);

    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    expect(
      screen.getByRole("tab", { name: "Conversation Summaries" }),
    ).toHaveAttribute("aria-selected", "true");
    const [newest, older] = screen.getAllByRole("listitem");
    expect(within(newest).getByText("Wed 11 Nov")).toBeVisible();
    expect(
      within(newest).getByText(
        "Talked through whether to accept the new role.",
      ),
    ).toBeVisible();
    expect(
      within(newest).getByText("You seemed unsettled at first, then calmer"),
    ).toBeVisible();
    expect(within(older).getByText("Mon 9 Nov")).toBeVisible();
  });

  it("deletes a Conversation Summary", async () => {
    const user = userEvent.setup();
    render(<Memories />);
    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete summary from Mon 9 Nov" }),
    );

    expect(apiClient.deleteConversationSummary).toHaveBeenCalledWith(
      "summary-2",
    );
    expect(
      screen.queryByText("A short Conversation after a morning swim."),
    ).not.toBeInTheDocument();
  });

  it("explains when there are no Conversation Summaries yet", async () => {
    apiClient.listConversationSummaries.mockResolvedValue([]);
    const user = userEvent.setup();
    render(<Memories />);

    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    expect(screen.getByText("No Conversation Summaries yet")).toBeVisible();
  });

  it("turns User Memory off and says what that means", async () => {
    apiClient.updatePreferences.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
    });
    const user = userEvent.setup();
    render(<Memories />);

    const memorySwitch = await screen.findByRole("switch", { name: "Memory" });
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Memory on")).toBeVisible();
    await user.click(memorySwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: false,
    });
    expect(await screen.findByText("Memory paused")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Memory is paused. Zeph won’t save anything new and won’t use what’s below until you turn it back on. Nothing has been deleted.",
    );
    expect(screen.getByText("Goes by Maya")).toBeVisible();
  });

  it("shows the notice straight away when User Memory is already off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    render(<Memories />);

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Memory is paused.",
    );
  });

  it("explains when nothing has been remembered yet", async () => {
    apiClient.listMemoryGroups.mockResolvedValue([]);
    render(<Memories />);

    expect(
      await screen.findByText("Zeph hasn’t remembered anything yet"),
    ).toBeVisible();
  });

  it("offers Try again when memories cannot be loaded", async () => {
    apiClient.listMemoryGroups
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(groups);
    const user = userEvent.setup();
    render(<Memories />);

    expect(
      await screen.findByText("We couldn’t load your memories"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
  });
});
