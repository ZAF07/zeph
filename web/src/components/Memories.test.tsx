import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Memories } from "@/components/Memories";
import type {
  ApiClient,
  ConversationSummary,
  LifeThread,
  MemoryGroup,
  SharedPhoto,
} from "@/lib/api-client";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
  listMemoryGroups: vi.fn<ApiClient["listMemoryGroups"]>(),
  deleteMemoryItem: vi.fn<ApiClient["deleteMemoryItem"]>(),
  deleteAllMemoryItems: vi.fn<ApiClient["deleteAllMemoryItems"]>(),
  listConversationSummaries: vi.fn<ApiClient["listConversationSummaries"]>(),
  deleteConversationSummary: vi.fn<ApiClient["deleteConversationSummary"]>(),
  listSharedPhotos: vi.fn<ApiClient["listSharedPhotos"]>(),
  getSharedPhotoImage: vi.fn<ApiClient["getSharedPhotoImage"]>(),
  deleteSharedPhoto: vi.fn<ApiClient["deleteSharedPhoto"]>(),
  listLifeThreads: vi.fn<ApiClient["listLifeThreads"]>(),
  deleteLifeThread: vi.fn<ApiClient["deleteLifeThread"]>(),
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

const lifeThreads: LifeThread[] = [
  {
    id: "thread-1",
    title: "Falling-out with Mei",
    story: "Fell out with their sister Mei in February over money.",
    is_open: true,
    updated_at: "2026-11-12T09:00:00Z",
  },
  {
    id: "thread-2",
    title: "Moving flat",
    story: "Moved into the new flat in March.",
    is_open: false,
    updated_at: "2026-10-03T09:00:00Z",
  },
];

const sharedPhotos: SharedPhoto[] = [
  {
    id: "photo-1",
    description: "A ginger cat asleep on a sunny windowsill.",
    note: "Miso is their cat, who keeps them company at home.",
    caption: "this is Miso",
    sent_at: "2026-11-10T09:00:00Z",
  },
  {
    id: "photo-2",
    description: "A hand-thrown blue mug on a kitchen counter.",
    note: "The first mug they made at their pottery class.",
    caption: "",
    sent_at: "2026-11-02T09:00:00Z",
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
    apiClient.listSharedPhotos.mockResolvedValue(sharedPhotos);
    apiClient.getSharedPhotoImage.mockResolvedValue(
      new Blob(["jpeg"], { type: "image/jpeg" }),
    );
    apiClient.deleteSharedPhoto.mockResolvedValue(undefined);
    apiClient.listLifeThreads.mockResolvedValue(lifeThreads);
    apiClient.deleteLifeThread.mockResolvedValue(undefined);
    URL.createObjectURL = vi.fn(() => "blob:photo");
    URL.revokeObjectURL = vi.fn();
  });

  it("marks User Memory as changed in chat with the day", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      changed_in_chat: { user_memory: "2026-11-03T09:00:00Z" },
    });
    renderWithQueries(<Memories />);

    expect(
      await screen.findByText("Changed in chat · 3 Nov"),
    ).toBeInTheDocument();
  });

  it("shows Memory Items grouped by Memory Category with where they came from", async () => {
    renderWithQueries(<Memories />);

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
    renderWithQueries(<Memories />);

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
    renderWithQueries(<Memories />);

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
    renderWithQueries(<Memories />);

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
    renderWithQueries(<Memories />);

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
    renderWithQueries(<Memories />);
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
    renderWithQueries(<Memories />);

    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    expect(screen.getByText("No Conversation Summaries yet")).toBeVisible();
  });

  it("shows each Life Thread's story, whether it is open, and when it was updated", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    await user.click(
      await screen.findByRole("tab", { name: "What’s going on" }),
    );

    expect(
      screen.getByRole("heading", { name: "What’s going on in your life" }),
    ).toBeVisible();
    const [open, settled] = screen.getAllByRole("listitem");
    expect(within(open).getByText("Falling-out with Mei")).toBeVisible();
    expect(
      within(open).getByText(
        "Fell out with their sister Mei in February over money.",
      ),
    ).toBeVisible();
    expect(within(open).getByText("Open")).toBeVisible();
    expect(within(open).getByText("Updated 12 Nov")).toBeVisible();
    expect(within(settled).getByText("Moving flat")).toBeVisible();
    expect(within(settled).getByText("Settled")).toBeVisible();
    expect(within(settled).getByText("Updated 3 Oct")).toBeVisible();
  });

  it("deletes a Life Thread", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories />);
    await user.click(
      await screen.findByRole("tab", { name: "What’s going on" }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Delete story: Falling-out with Mei",
      }),
    );

    expect(apiClient.deleteLifeThread).toHaveBeenCalledWith("thread-1");
    expect(screen.queryByText("Falling-out with Mei")).not.toBeInTheDocument();
    expect(screen.getByText("Moving flat")).toBeVisible();
  });

  it("keeps a Life Thread and explains when deleting it fails", async () => {
    apiClient.deleteLifeThread.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories />);
    await user.click(
      await screen.findByRole("tab", { name: "What’s going on" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete story: Moving flat" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(screen.getByText("Moving flat")).toBeVisible();
  });

  it("explains when there are no Life Threads yet", async () => {
    apiClient.listLifeThreads.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    await user.click(
      await screen.findByRole("tab", { name: "What’s going on" }),
    );

    expect(screen.getByText("Nothing here yet")).toBeVisible();
  });

  it("still shows and deletes Life Threads when User Memory is off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    const user = userEvent.setup();
    renderWithQueries(<Memories />);
    await user.click(
      await screen.findByRole("tab", { name: "What’s going on" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete story: Moving flat" }),
    );

    expect(apiClient.deleteLifeThread).toHaveBeenCalledWith("thread-2");
  });

  it("shows each Shared Photo with its photo, description, note and date", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    const cat = within(
      screen.getByRole("listitem", { name: "Photo from Tue 10 Nov" }),
    );
    expect(
      await cat.findByAltText("A ginger cat asleep on a sunny windowsill."),
    ).toHaveAttribute("src", "blob:photo");
    expect(
      cat.getByText("A ginger cat asleep on a sunny windowsill."),
    ).toBeVisible();
    expect(
      cat.getByText("Miso is their cat, who keeps them company at home."),
    ).toBeVisible();
    expect(cat.getByText("Tue 10 Nov")).toBeVisible();
    expect(apiClient.getSharedPhotoImage).toHaveBeenCalledWith("photo-1");
    expect(apiClient.getSharedPhotoImage).toHaveBeenCalledWith("photo-2");
  });

  it("says so when a Shared Photo's image can't be loaded", async () => {
    apiClient.getSharedPhotoImage.mockRejectedValue(new Error("gone"));
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    expect(
      await screen.findAllByText("This photo can’t be shown right now"),
    ).toHaveLength(2);
    expect(
      screen.getByText("A ginger cat asleep on a sunny windowsill."),
    ).toBeVisible();
  });

  it("deletes a Shared Photo", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories />);
    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    await user.click(
      screen.getByRole("button", { name: "Delete photo from Mon 2 Nov" }),
    );

    expect(apiClient.deleteSharedPhoto).toHaveBeenCalledWith("photo-2");
    expect(
      screen.queryByText("A hand-thrown blue mug on a kitchen counter."),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("A ginger cat asleep on a sunny windowsill."),
    ).toBeVisible();
  });

  it("keeps a Shared Photo and explains when deleting it fails", async () => {
    apiClient.deleteSharedPhoto.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories />);
    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    await user.click(
      screen.getByRole("button", { name: "Delete photo from Mon 2 Nov" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(
      screen.getByText("A hand-thrown blue mug on a kitchen counter."),
    ).toBeVisible();
  });

  it("explains when there are no Shared Photos yet", async () => {
    apiClient.listSharedPhotos.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    expect(screen.getByText("No photos kept yet")).toBeVisible();
  });

  it("turns User Memory off and says what that means", async () => {
    apiClient.updatePreferences.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
      memory_note:
        "**Memory is paused.** Zeph won’t learn anything new, but still uses what it already knows about you.",
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    const memorySwitch = await screen.findByRole("switch", { name: "Memory" });
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Memory on")).toBeVisible();
    await user.click(memorySwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: false,
    });
    expect(await screen.findByText("Memory paused")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Memory is paused. Zeph won’t learn anything new, but still uses what it already knows about you.",
    );
    expect(screen.getByText("Goes by Maya")).toBeVisible();
  });

  it("shows the notice straight away when User Memory is already off", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
      memory_note:
        "**Memory is paused.** Zeph won’t learn anything new, but still uses what it already knows about you.",
    });
    renderWithQueries(<Memories />);

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Memory is paused.",
    );
  });

  it("shows Not available on your account with the switch disabled, and memories still deletable", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_available: false,
      memory_note:
        "**Memory isn’t available on your account.** Zeph won’t learn anything new.",
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    const memorySwitch = await screen.findByRole("switch", { name: "Memory" });
    expect(memorySwitch).toBeDisabled();
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Not available on your account")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Memory isn’t available on your account. Zeph won’t learn anything new.",
    );
    await user.click(memorySwitch);
    expect(apiClient.updatePreferences).not.toHaveBeenCalled();

    await user.click(
      screen.getByRole("button", { name: "Delete memory: Goes by Maya" }),
    );
    expect(apiClient.deleteMemoryItem).toHaveBeenCalledWith("item-2");
  });

  it("explains when nothing has been remembered yet", async () => {
    apiClient.listMemoryGroups.mockResolvedValue([]);
    renderWithQueries(<Memories />);

    expect(
      await screen.findByText("Zeph hasn’t remembered anything yet"),
    ).toBeVisible();
  });

  it("offers Try again when memories cannot be loaded", async () => {
    apiClient.listMemoryGroups
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(groups);
    const user = userEvent.setup();
    renderWithQueries(<Memories />);

    expect(
      await screen.findByText("We couldn’t load your memories"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
  });
});
