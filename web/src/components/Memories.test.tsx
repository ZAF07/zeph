import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Memories } from "@/components/Memories";
import type {
  ApiClient,
  DaySummary,
  KeptQuote,
  LifeThread,
  MemoryGroup,
  MoveOutcome,
  Pattern,
  SharedPhoto,
  UserPortrait,
} from "@/lib/api-client";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";
import { userWithRole } from "@/test/fixtures";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  updatePreferences: vi.fn<ApiClient["updatePreferences"]>(),
  listMemoryGroups: vi.fn<ApiClient["listMemoryGroups"]>(),
  deleteMemoryItem: vi.fn<ApiClient["deleteMemoryItem"]>(),
  deleteAllMemoryItems: vi.fn<ApiClient["deleteAllMemoryItems"]>(),
  listDaySummaries: vi.fn<ApiClient["listDaySummaries"]>(),
  deleteDaySummary: vi.fn<ApiClient["deleteDaySummary"]>(),
  listSharedPhotos: vi.fn<ApiClient["listSharedPhotos"]>(),
  getSharedPhotoImage: vi.fn<ApiClient["getSharedPhotoImage"]>(),
  deleteSharedPhoto: vi.fn<ApiClient["deleteSharedPhoto"]>(),
  listLifeThreads: vi.fn<ApiClient["listLifeThreads"]>(),
  deleteLifeThread: vi.fn<ApiClient["deleteLifeThread"]>(),
  listPatterns: vi.fn<ApiClient["listPatterns"]>(),
  deletePattern: vi.fn<ApiClient["deletePattern"]>(),
  listKeptQuotes: vi.fn<ApiClient["listKeptQuotes"]>(),
  deleteKeptQuote: vi.fn<ApiClient["deleteKeptQuote"]>(),
  markPatternNoticingTold: vi.fn<ApiClient["markPatternNoticingTold"]>(),
  listMoveOutcomes: vi.fn<ApiClient["listMoveOutcomes"]>(),
  deleteMoveOutcome: vi.fn<ApiClient["deleteMoveOutcome"]>(),
  getUserPortrait: vi.fn<ApiClient["getUserPortrait"]>(),
  deleteUserPortrait: vi.fn<ApiClient["deleteUserPortrait"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const navigation = { search: "" };

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(navigation.search),
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

const summaries: DaySummary[] = [
  {
    id: "summary-1",
    summary: "Talked through whether to accept the new role.",
    mood: "unsettled at first, then calmer",
    offered: "Suggested a walk; they said it helped.",
    day: "2026-11-11",
    written_at: "2026-11-11T23:30:00Z",
  },
  {
    id: "summary-2",
    summary: "A short Conversation after a morning swim.",
    mood: "light and content",
    offered: "",
    day: "2026-11-09",
    written_at: "2026-11-09T09:00:00Z",
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

const moveOutcomes: MoveOutcome[] = [
  {
    id: "outcome-1",
    move: "Push",
    role: "lead",
    situation: "Their launch kept slipping; they couldn’t say what done meant.",
    feeling: "frustrated, a bit stuck",
    result: "helped",
    why: "Pinning down a finish line gave them a next step they took.",
    made_at: "2026-11-14T09:00:00Z",
  },
  {
    id: "outcome-2",
    move: "Plan steps",
    role: "support",
    situation: "Planning the week after a long day.",
    feeling: "exhausted",
    result: "didnt_help",
    why: "Too much to take in while they were worn out.",
    made_at: "2026-11-08T09:00:00Z",
  },
];

const patterns: Pattern[] = [
  {
    id: "pattern-1",
    state: "shared",
    pattern: "You seem to treat rest as something to be earned.",
    where_it_shows: [],
    told_at: "2026-11-12T09:00:00Z",
    quote_groups: [
      {
        life_thread: "Pushing hard at work",
        quotes: [
          { quote: "If I stop now, I fall behind.", day: "2026-11-12" },
          { quote: "I worked the whole weekend.", day: "2026-11-08" },
        ],
      },
      {
        life_thread: null,
        quotes: [{ quote: "I felt guilty all afternoon.", day: "2026-11-02" }],
      },
    ],
    predictions: [
      {
        wording: "Next time you take an evening off, notice what you do.",
        made_at: "2026-11-12T09:00:00Z",
        outcome: null,
      },
    ],
  },
  {
    id: "pattern-2",
    state: "confirmed",
    pattern: "You seem to name the worst version of a plan first.",
    where_it_shows: [
      {
        condition: "relationship",
        shows_with: ["family", "friend"],
        not_with: ["colleague"],
      },
      {
        condition: "audience",
        shows_with: ["group"],
        not_with: ["one-to-one"],
      },
      {
        condition: "state_going_in",
        shows_with: ["worn out"],
        not_with: ["steady"],
      },
    ],
    told_at: "2026-11-01T09:00:00Z",
    quote_groups: [
      {
        life_thread: "The new job",
        quotes: [{ quote: "I'll mess up the first week.", day: "2026-10-28" }],
      },
    ],
    predictions: [
      {
        wording: "Next time you share a plan, notice how you start.",
        made_at: "2026-11-01T09:00:00Z",
        outcome: "came_true",
      },
    ],
  },
  {
    id: "pattern-3",
    state: "contested",
    pattern: "You seem to keep disagreements small.",
    where_it_shows: [],
    told_at: "2026-11-05T09:00:00Z",
    quote_groups: [],
    predictions: [],
  },
  {
    id: "pattern-4",
    state: "closed",
    pattern: "You seem to check things are alright after a disagreement.",
    where_it_shows: [],
    told_at: "2026-10-20T09:00:00Z",
    quote_groups: [],
    predictions: [
      {
        wording: "Next time you disagree at work, notice what you do after.",
        made_at: "2026-10-20T09:00:00Z",
        outcome: "did_not",
      },
    ],
  },
];

const keptQuotes: KeptQuote[] = [
  {
    id: "quote-1",
    quote: "If I stop now, everyone will see I can't keep up.",
    context: "Talking about working through the weekend.",
    day: "2026-11-12",
  },
  {
    id: "quote-2",
    quote: "It's probably just me running away again.",
    context: "Talking about the van trip.",
    day: "2026-11-09",
  },
];

const portrait: UserPortrait = {
  text: "Maya is a designer weighing a new role. Walks help; pep talks don’t.",
  updated_at: "2026-11-13T09:00:00Z",
};

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
    navigation.search = "";
    window.history.replaceState({}, "", "/memories");
    apiClient.getMe.mockResolvedValue(maya);
    apiClient.listMemoryGroups.mockResolvedValue(groups);
    apiClient.listDaySummaries.mockResolvedValue(summaries);
    apiClient.deleteMemoryItem.mockResolvedValue(undefined);
    apiClient.deleteAllMemoryItems.mockResolvedValue(undefined);
    apiClient.deleteDaySummary.mockResolvedValue(undefined);
    apiClient.listSharedPhotos.mockResolvedValue(sharedPhotos);
    apiClient.getSharedPhotoImage.mockResolvedValue(
      new Blob(["jpeg"], { type: "image/jpeg" }),
    );
    apiClient.deleteSharedPhoto.mockResolvedValue(undefined);
    apiClient.listLifeThreads.mockResolvedValue(lifeThreads);
    apiClient.deleteLifeThread.mockResolvedValue(undefined);
    apiClient.listPatterns.mockResolvedValue(patterns);
    apiClient.deletePattern.mockResolvedValue(undefined);
    apiClient.listKeptQuotes.mockResolvedValue(keptQuotes);
    apiClient.deleteKeptQuote.mockResolvedValue(undefined);
    apiClient.listMoveOutcomes.mockResolvedValue(moveOutcomes);
    apiClient.deleteMoveOutcome.mockResolvedValue(undefined);
    apiClient.getUserPortrait.mockResolvedValue(portrait);
    apiClient.deleteUserPortrait.mockResolvedValue(undefined);
    URL.createObjectURL = vi.fn(() => "blob:photo");
    URL.revokeObjectURL = vi.fn();
  });

  it("swaps the panel and sets ?tab= when a tab is clicked, without a page load", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    const memoriesTab = await screen.findByRole("tab", { name: "Memories" });

    await user.click(screen.getByRole("tab", { name: "Photos" }));

    expect(window.location.pathname).toBe("/memories");
    expect(window.location.search).toBe("?tab=photos");
    expect(screen.getByRole("tab", { name: "Photos" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("heading", { name: "Photos" })).toBeVisible();
    expect(screen.queryByText("Goes by Maya")).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Memories" })).toBe(memoriesTab);

    await user.click(memoriesTab);

    expect(window.location.search).toBe("");
    expect(screen.getByText("Goes by Maya")).toBeVisible();
  });

  it("keeps other query flags when it sets ?tab=", async () => {
    navigation.search = "design=menu-open";
    window.history.replaceState({}, "", "/memories?design=menu-open");
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "About you" }));

    expect(window.location.search).toBe("?design=menu-open&tab=about");
  });

  it.each([
    ["about", "About you", "What I know about you"],
    ["threads", "What's going on", "What's going on in your life"],
    ["patterns", "Patterns", "Patterns"],
    ["helps", "What helps you", "What helps you"],
    ["summaries", "Conversation Summaries", "Conversation Summaries"],
    ["photos", "Photos", "Photos"],
  ])(
    "opens the %s tab when loaded with ?tab=",
    async (tab, tabName, heading) => {
      navigation.search = `tab=${tab}`;
      renderWithQueries(<Memories copy={seedCopy()} />);

      expect(
        await screen.findByRole("heading", { name: heading }),
      ).toBeVisible();
      expect(screen.getByRole("tab", { name: tabName })).toHaveAttribute(
        "aria-selected",
        "true",
      );
    },
  );

  it("opens the Memories tab when ?tab= is unknown", async () => {
    navigation.search = "tab=nonsense";
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
    expect(screen.getByRole("tab", { name: "Memories" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("marks User Memory as changed in chat with the day", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      changed_in_chat: { user_memory: "2026-11-03T09:00:00Z" },
    });
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(
      await screen.findByText("Changed in chat · 3 Nov"),
    ).toBeInTheDocument();
  });

  it("shows Memory Items grouped by Memory Category with where they came from", async () => {
    renderWithQueries(<Memories copy={seedCopy()} />);

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
  });

  it("deletes a single Memory Item", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

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
  });

  it("keeps a Memory Item and explains when deleting it fails", async () => {
    apiClient.deleteMemoryItem.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

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
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("button", { name: "Delete all memories" }),
    );
    const dialog = within(
      screen.getByRole("alertdialog", { name: "Delete all memories?" }),
    );
    expect(
      dialog.getByText(
        "Zeph will forget every memory it holds about you. Conversation Summaries and your account stay. This can’t be undone.",
      ),
    ).toBeVisible();
    await user.click(dialog.getByRole("button", { name: "Keep them" }));
    expect(apiClient.deleteAllMemoryItems).not.toHaveBeenCalled();
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Delete all memories" }),
    );
    await user.click(
      within(
        screen.getByRole("alertdialog", { name: "Delete all memories?" }),
      ).getByRole("button", { name: "Delete all memories" }),
    );

    expect(apiClient.deleteAllMemoryItems).toHaveBeenCalledOnce();
    expect(await screen.findByText("Nothing remembered yet")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Delete all memories" }),
    ).not.toBeInTheDocument();
  });

  it("lists one Summary per day, by its day, with how the User seemed", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    expect(
      screen.getByRole("tab", { name: "Conversation Summaries" }),
    ).toHaveAttribute("aria-selected", "true");
    const [newest, older] = screen.getAllByRole("listitem");
    expect(within(newest).getByText("11 Nov")).toBeVisible();
    expect(
      within(newest).getByText(
        "Talked through whether to accept the new role.",
      ),
    ).toBeVisible();
    expect(within(newest).getByText("Seemed")).toBeVisible();
    expect(
      within(newest).getByText("unsettled at first, then calmer"),
    ).toBeVisible();
    expect(within(newest).getByText("Zeph offered")).toBeVisible();
    expect(
      within(newest).getByText("Suggested a walk; they said it helped."),
    ).toBeVisible();
    expect(within(older).getByText("9 Nov")).toBeVisible();
    expect(within(older).queryByText("Zeph offered")).not.toBeInTheDocument();
  });

  it("deletes a Day Summary", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete summary from 9 Nov" }),
    );

    expect(apiClient.deleteDaySummary).toHaveBeenCalledWith("summary-2");
    expect(
      screen.queryByText("A short Conversation after a morning swim."),
    ).not.toBeInTheDocument();
  });

  it("explains when there are no Day Summaries yet", async () => {
    apiClient.listDaySummaries.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "Conversation Summaries" }),
    );

    expect(screen.getByText("No Conversation Summaries yet")).toBeVisible();
  });

  it("shows what Zeph knows about the User and when it was updated", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "About you" }));

    expect(
      screen.getByRole("heading", { name: "What I know about you" }),
    ).toBeVisible();
    expect(screen.getByText(portrait.text)).toBeVisible();
    expect(screen.getByText("Written 13 Nov")).toBeVisible();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("deletes what Zeph knows about the User", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "About you" }));

    await user.click(
      screen.getByRole("button", { name: "Delete what Zeph knows about you" }),
    );

    expect(apiClient.deleteUserPortrait).toHaveBeenCalled();
    expect(screen.queryByText(portrait.text)).not.toBeInTheDocument();
    expect(screen.getByText("Nothing here yet")).toBeVisible();
  });

  it("keeps the Portrait and explains when deleting it fails", async () => {
    apiClient.deleteUserPortrait.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "About you" }));

    await user.click(
      screen.getByRole("button", { name: "Delete what Zeph knows about you" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(screen.getByText(portrait.text)).toBeVisible();
  });

  it("explains when there is no Portrait yet", async () => {
    apiClient.getUserPortrait.mockResolvedValue(null);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "About you" }));

    expect(screen.getByText("Nothing here yet")).toBeVisible();
  });

  it("still shows and deletes the Portrait when User Memory is off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "About you" }));

    await user.click(
      screen.getByRole("button", { name: "Delete what Zeph knows about you" }),
    );

    expect(apiClient.deleteUserPortrait).toHaveBeenCalled();
  });

  it("shows each Life Thread's story, whether it is open, and when it was updated", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "What's going on" }),
    );

    expect(
      screen.getByRole("heading", { name: "What's going on in your life" }),
    ).toBeVisible();
    const [open, closed] = screen.getAllByRole("listitem");
    expect(within(open).getByText("Falling-out with Mei")).toBeVisible();
    expect(
      within(open).getByText(
        "Fell out with their sister Mei in February over money.",
      ),
    ).toBeVisible();
    expect(within(open).getByText("Open")).toBeVisible();
    expect(within(open).getByText("Updated 12 Nov")).toBeVisible();
    expect(within(closed).getByText("Moving flat")).toBeVisible();
    expect(within(closed).getByText("Closed")).toBeVisible();
    expect(within(closed).getByText("Updated 3 Oct")).toBeVisible();
  });

  it("deletes a Life Thread", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "What's going on" }),
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
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "What's going on" }),
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
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "What's going on" }),
    );

    expect(screen.getByText("Nothing here yet")).toBeVisible();
  });

  it("still shows and deletes Life Threads when User Memory is off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "What's going on" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete story: Moving flat" }),
    );

    expect(apiClient.deleteLifeThread).toHaveBeenCalledWith("thread-2");
  });

  it("shows the Patterns Zeph told the User under four headings, with quotes by part of life and what to notice", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    expect(screen.getByRole("heading", { name: "Patterns" })).toBeVisible();
    const tested = within(screen.getByRole("region", { name: "Being tested" }));
    expect(
      tested.getByText("You seem to treat rest as something to be earned."),
    ).toBeVisible();
    expect(tested.getByText("Zeph told you this on 12 Nov")).toBeVisible();
    expect(tested.getByText("In your own words")).toBeVisible();
    const work = tested.getByText("Pushing hard at work").parentElement!;
    expect(work).toHaveTextContent(
      "“If I stop now, I fall behind.”12 Nov“I worked the whole weekend.”8 Nov",
    );
    const noThread = tested.getByText("Other moments").parentElement!;
    expect(noThread).toHaveTextContent("“I felt guilty all afternoon.”2 Nov");
    expect(tested.getByText("What Zeph asked you to notice")).toBeVisible();
    const asked = tested.getByText("Asked on 12 Nov").parentElement!;
    expect(asked).toHaveTextContent(
      "Next time you take an evening off, notice what you do.Zeph hasn't asked how it went yet.",
    );

    const confirmed = within(screen.getByRole("region", { name: "Confirmed" }));
    expect(
      confirmed.getByText(
        "You seem to name the worst version of a plan first.",
      ),
    ).toBeVisible();
    expect(
      confirmed.getByText("It shows with family, friend; not with colleague."),
    ).toBeVisible();
    expect(
      confirmed.getByText("It shows in a group; not one-to-one."),
    ).toBeVisible();
    expect(
      confirmed.getByText(
        "It shows on days you were worn out; not on days you felt steady.",
      ),
    ).toBeVisible();
    expect(
      confirmed.getByText("How it went: it happened as Zeph thought."),
    ).toBeVisible();

    const disagreed = within(
      screen.getByRole("region", { name: "You disagreed" }),
    );
    expect(
      disagreed.getByText("You seem to keep disagreements small."),
    ).toBeVisible();
    expect(disagreed.queryByText("In your own words")).not.toBeInTheDocument();

    const closed = within(
      screen.getByRole("region", { name: "Didn't hold up" }),
    );
    expect(
      closed.getByText("How it went: it didn't happen as Zeph thought."),
    ).toBeVisible();
    expect(
      screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent),
    ).toEqual(["Being tested", "Confirmed", "You disagreed", "Didn't hold up"]);
  });

  it("shows no heading for a kind of Pattern the User has none of", async () => {
    apiClient.listPatterns.mockResolvedValue([patterns[1]]);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    expect(
      screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent),
    ).toEqual(["Confirmed"]);
    expect(
      screen.queryByRole("switch", { name: "Keep noticing after I disagree" }),
    ).not.toBeInTheDocument();
  });

  it("lets the User stop Zeph noting evidence for Patterns they disagreed with", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      contested_gathering_enabled: true,
    });
    apiClient.updatePreferences.mockResolvedValue({
      ...maya,
      contested_gathering_enabled: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Patterns" }));
    const disagreed = within(
      screen.getByRole("region", { name: "You disagreed" }),
    );

    await user.click(
      disagreed.getByRole("switch", { name: "Keep noticing after I disagree" }),
    );

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      contested_gathering_enabled: false,
    });
  });

  it("deletes a Pattern", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    await user.click(
      screen.getByRole("button", {
        name: "Delete pattern: You seem to treat rest as something to be earned.",
      }),
    );

    expect(apiClient.deletePattern).toHaveBeenCalledWith("pattern-1");
    expect(
      screen.queryByText("You seem to treat rest as something to be earned."),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Being tested")).not.toBeInTheDocument();
    expect(
      screen.getByText("You seem to name the worst version of a plan first."),
    ).toBeVisible();
  });

  it("keeps a Pattern and explains when deleting it fails", async () => {
    apiClient.deletePattern.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    await user.click(
      screen.getByRole("button", {
        name: "Delete pattern: You seem to treat rest as something to be earned.",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(
      screen.getByText("You seem to treat rest as something to be earned."),
    ).toBeVisible();
  });

  it("explains when Zeph has told the User no Pattern yet", async () => {
    apiClient.listPatterns.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    expect(screen.getByText("No patterns yet")).toBeVisible();
    expect(
      screen.getByText(
        "When Zeph tells you about something it has noticed across different parts of your life, it appears here with your own words behind it.",
      ),
    ).toBeVisible();
  });

  it("still shows and deletes Patterns when User Memory is off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Patterns" }));

    await user.click(
      screen.getByRole("button", {
        name: "Delete pattern: You seem to name the worst version of a plan first.",
      }),
    );

    expect(apiClient.deletePattern).toHaveBeenCalledWith("pattern-2");
  });

  it("lists each kept quote apart from Zeph's note, with its day, newest first", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "Things you said" }),
    );

    expect(
      screen.getByRole("heading", { name: "Things you said that Zeph kept" }),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Your exact words that Zeph keeps to notice what you do again and again. They stay after your messages are deleted, until you delete them. Delete one and Zeph stops using it.",
      ),
    ).toBeVisible();
    const [newest, older] = screen.getAllByRole("listitem");
    const quote = within(newest).getByText(
      "“If I stop now, everyone will see I can't keep up.”",
    );
    const note = within(newest).getByText(
      "Talking about working through the weekend.",
    );
    expect(quote).not.toBe(note);
    expect(quote).not.toContainElement(note);
    expect(within(newest).getByText("Zeph's note")).toBeVisible();
    expect(within(newest).getByText("You said this on 12 Nov")).toBeVisible();
    expect(within(older).getByText("You said this on 9 Nov")).toBeVisible();
    expect(
      within(screen.getByRole("tabpanel")).queryByText(/pattern/i),
    ).toBeNull();
  });

  it("deletes a kept quote at once", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "Things you said" }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Delete quote: If I stop now, everyone will see I can't keep up.",
      }),
    );

    expect(apiClient.deleteKeptQuote).toHaveBeenCalledWith("quote-1");
    expect(
      screen.queryByText("“If I stop now, everyone will see I can't keep up.”"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("“It's probably just me running away again.”"),
    ).toBeVisible();
  });

  it("keeps a kept quote and explains when deleting it fails", async () => {
    apiClient.deleteKeptQuote.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "Things you said" }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Delete quote: It's probably just me running away again.",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(
      screen.getByText("“It's probably just me running away again.”"),
    ).toBeVisible();
  });

  it("explains when no quote is kept yet", async () => {
    apiClient.listKeptQuotes.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "Things you said" }),
    );

    expect(screen.getByText("Nothing kept yet")).toBeVisible();
    expect(
      screen.getByText(
        "When something you say helps Zeph notice what you do again and again, it may keep your exact words here after the Conversation ends.",
      ),
    ).toBeVisible();
  });

  it("still shows and deletes kept quotes when User Memory is off", async () => {
    apiClient.getMe.mockResolvedValue({ ...maya, user_memory_enabled: false });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "Things you said" }),
    );

    await user.click(
      screen.getByRole("button", {
        name: "Delete quote: It's probably just me running away again.",
      }),
    );

    expect(apiClient.deleteKeptQuote).toHaveBeenCalledWith("quote-2");
  });

  it("tells the User what changed until they press Got it", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      show_pattern_noticing_notice: true,
    });
    apiClient.markPatternNoticingTold.mockResolvedValue({
      ...maya,
      show_pattern_noticing_notice: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(
      await screen.findByText("Zeph now keeps some of your words."),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Got it" }));

    expect(apiClient.markPatternNoticingTold).toHaveBeenCalled();
    expect(
      screen.queryByText("Zeph now keeps some of your words."),
    ).not.toBeInTheDocument();
  });

  it("keeps the notice and explains when Got it can't be saved", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      show_pattern_noticing_notice: true,
    });
    apiClient.markPatternNoticingTold.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("button", { name: "Got it" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t save that. Please try again.",
    );
    expect(
      screen.getByText("Zeph now keeps some of your words."),
    ).toBeVisible();
  });

  it("shows no notice once the User has been told", async () => {
    renderWithQueries(<Memories copy={seedCopy()} />);

    await screen.findByRole("tabpanel");

    expect(
      screen.queryByText("Zeph now keeps some of your words."),
    ).not.toBeInTheDocument();
  });

  it("shows what helps: each Move Outcome's situation, feeling, result, why and date", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "What helps you" }),
    );

    expect(
      screen.getByRole("heading", { name: "What helps you" }),
    ).toBeVisible();
    const [push, planSteps] = screen.getAllByRole("listitem");
    expect(within(push).getByText("Push")).toBeVisible();
    expect(within(push).getByText("Helped")).toBeVisible();
    expect(within(push).getByText("When")).toBeVisible();
    expect(
      within(push).getByText(
        "Their launch kept slipping; they couldn’t say what done meant.",
      ),
    ).toBeVisible();
    expect(within(push).getByText("Feeling")).toBeVisible();
    expect(within(push).getByText("frustrated, a bit stuck")).toBeVisible();
    expect(within(push).getByText("Why")).toBeVisible();
    expect(
      within(push).getByText(
        "Pinning down a finish line gave them a next step they took.",
      ),
    ).toBeVisible();
    expect(within(push).getByText("14 Nov")).toBeVisible();
    expect(within(planSteps).getByText("Plan steps")).toBeVisible();
    expect(within(planSteps).getByText("Didn’t help")).toBeVisible();
  });

  it("deletes a Move Outcome", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "What helps you" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete what helps: Push, 14 Nov" }),
    );

    expect(apiClient.deleteMoveOutcome).toHaveBeenCalledWith("outcome-1");
    expect(screen.queryByText("Push")).not.toBeInTheDocument();
    expect(screen.getByText("Plan steps")).toBeVisible();
  });

  it("keeps a Move Outcome and explains when deleting it fails", async () => {
    apiClient.deleteMoveOutcome.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(
      await screen.findByRole("tab", { name: "What helps you" }),
    );

    await user.click(
      screen.getByRole("button", { name: "Delete what helps: Push, 14 Nov" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn’t delete that. Please try again.",
    );
    expect(screen.getByText("Push")).toBeVisible();
  });

  it("explains when nothing is known yet about what helps", async () => {
    apiClient.listMoveOutcomes.mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("tab", { name: "What helps you" }),
    );

    expect(screen.getByText("Nothing here yet")).toBeVisible();
  });

  it("shows each Shared Photo with its photo, description, note and date", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    const cat = within(screen.getAllByRole("listitem")[0]);
    expect(
      await cat.findByAltText("A ginger cat asleep on a sunny windowsill."),
    ).toHaveAttribute("src", "blob:photo");
    expect(
      cat.getByText("A ginger cat asleep on a sunny windowsill."),
    ).toBeVisible();
    expect(
      cat.getByText("Miso is their cat, who keeps them company at home."),
    ).toBeVisible();
    expect(cat.getByText("Sent 10 Nov")).toBeVisible();
    expect(apiClient.getSharedPhotoImage).toHaveBeenCalledWith("photo-1");
    expect(apiClient.getSharedPhotoImage).toHaveBeenCalledWith("photo-2");
  });

  it("says so when a Shared Photo's image can't be loaded", async () => {
    apiClient.getSharedPhotoImage.mockRejectedValue(new Error("gone"));
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    expect(
      await screen.findAllByText("This photo can’t be shown right now"),
    ).toHaveLength(2);
    expect(
      screen.getByRole("img", { name: "Photo from 10 Nov" }),
    ).toHaveTextContent("This photo can’t be shown right now");
    expect(
      screen.getByText("A ginger cat asleep on a sunny windowsill."),
    ).toBeVisible();
  });

  it("deletes a Shared Photo", async () => {
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    await user.click(
      screen.getByRole("button", { name: "Delete photo from 2 Nov" }),
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
    renderWithQueries(<Memories copy={seedCopy()} />);
    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    await user.click(
      screen.getByRole("button", { name: "Delete photo from 2 Nov" }),
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
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(await screen.findByRole("tab", { name: "Photos" }));

    expect(screen.getByText("No photos kept yet")).toBeVisible();
  });

  it("turns User Memory off and says what that means", async () => {
    apiClient.updatePreferences.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    const memorySwitch = await screen.findByRole("switch", { name: "Memory" });
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Memory on")).toBeVisible();
    await user.click(memorySwitch);

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: false,
    });
    expect(await screen.findByText("Memory paused")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      `Memory is paused.${seedCopy()["shared.memory_off.paused_body"]}`,
    );
    expect(screen.getByText("Goes by Maya")).toBeVisible();
  });

  it("shows the notice straight away when User Memory is already off", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
    });
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Memory is paused.");
  });

  it("draws the paused note's title and body from Copy as the notice's title and body", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
    });
    const copy = {
      ...seedCopy(),
      "shared.memory_off.paused_title": "Zeph is resting.",
      "shared.memory_off.paused_body": "Nothing is deleted. Back soon.",
    };
    renderWithQueries(<Memories copy={copy} />);

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
    const notice = screen.getByRole("status");
    expect(within(notice).getByText("Zeph is resting.")).toHaveClass(
      "text-[15px]",
      "text-text",
    );
    expect(
      within(notice).getByText("Nothing is deleted. Back soon."),
    ).toHaveClass("text-[13px]", "text-soft");
  });

  it("turns User Memory back on from the notice", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_enabled: false,
    });
    apiClient.updatePreferences.mockResolvedValue(maya);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    await user.click(
      await screen.findByRole("button", { name: "Turn memory on" }),
    );

    expect(apiClient.updatePreferences).toHaveBeenCalledWith({
      user_memory_enabled: true,
    });
    expect(await screen.findByText("Memory on")).toBeVisible();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows Not available on your account with the switch disabled, and memories still deletable", async () => {
    apiClient.getMe.mockResolvedValue({
      ...maya,
      user_memory_available: false,
    });
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    const memorySwitch = await screen.findByRole("switch", { name: "Memory" });
    expect(memorySwitch).toBeDisabled();
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("Not available on your account")).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent(
      `Memory isn’t available on your account.${seedCopy()["shared.memory_off.not_available_body"]}`,
    );
    await user.click(memorySwitch);
    expect(apiClient.updatePreferences).not.toHaveBeenCalled();
    expect(
      screen.queryByRole("button", { name: "Turn memory on" }),
    ).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Delete memory: Goes by Maya" }),
    );
    expect(apiClient.deleteMemoryItem).toHaveBeenCalledWith("item-2");
  });

  it("explains when nothing has been remembered yet", async () => {
    apiClient.listMemoryGroups.mockResolvedValue([]);
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(await screen.findByText("Nothing remembered yet")).toBeVisible();
    expect(screen.getByRole("link", { name: "Talk to Zeph" })).toBeVisible();
  });

  it("offers Try again when memories cannot be loaded", async () => {
    apiClient.listMemoryGroups
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(groups);
    const user = userEvent.setup();
    renderWithQueries(<Memories copy={seedCopy()} />);

    expect(
      await screen.findByText("Couldn’t load your memories"),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Goes by Maya")).toBeVisible();
  });

  describe("reads every word from Copy", () => {
    const tabSlots = [
      "memories",
      "about",
      "threads",
      "patterns",
      "helps",
      "summaries",
      "photos",
      "quotes",
    ];

    /**
     * Says what words on the page did not come from Copy, leaving out the
     * days shown on their own, like "12 Nov", which are values, not words.
     *
     * @param container - The rendered page.
     * @returns Each piece of text not from Copy or a day.
     */
    function wordsNotFromCopyOrDays(container: HTMLElement): string[] {
      const words = container.cloneNode(true) as HTMLElement;
      words.querySelectorAll("span").forEach((span) => {
        if (/^\d{1,2} [A-Z][a-z]{2,3}$/.test(span.textContent ?? "")) {
          span.remove();
        }
      });
      return wordsNotFromCopy(words);
    }

    function markData() {
      apiClient.listMemoryGroups.mockResolvedValue(
        groups.map((group) => ({
          category: "⟦data⟧",
          items: group.items.map((item) => ({ ...item, content: "⟦data⟧" })),
        })),
      );
      apiClient.getUserPortrait.mockResolvedValue({
        ...portrait,
        text: "⟦data⟧",
      });
      apiClient.listLifeThreads.mockResolvedValue(
        lifeThreads.map((thread) => ({
          ...thread,
          title: "⟦data⟧",
          story: "⟦data⟧",
        })),
      );
      apiClient.listPatterns.mockResolvedValue(
        patterns.map((pattern) => ({
          ...pattern,
          pattern: "⟦data⟧",
          where_it_shows: [
            {
              condition: "relationship",
              shows_with: ["family"],
              not_with: ["partner"],
            },
            { condition: "stakes", shows_with: ["high"], not_with: ["low"] },
          ],
          quote_groups: [
            {
              life_thread: "⟦data⟧",
              quotes: [{ quote: "⟦data⟧", day: "2026-11-12" }],
            },
            {
              life_thread: null,
              quotes: [{ quote: "⟦data⟧", day: "2026-11-02" }],
            },
          ],
          predictions: (
            [
              "came_true",
              "did_not",
              "not_come_up",
              "not_followed_up",
              null,
            ] as const
          ).map((outcome) => ({
            wording: "⟦data⟧",
            made_at: "2026-11-12T09:00:00Z",
            outcome,
          })),
        })),
      );
      apiClient.listKeptQuotes.mockResolvedValue(
        keptQuotes.map((quote) => ({
          ...quote,
          quote: "⟦data⟧",
          context: "⟦data⟧",
        })),
      );
      apiClient.listMoveOutcomes.mockResolvedValue(
        moveOutcomes.map((outcome) => ({
          ...outcome,
          move: "⟦data⟧",
          situation: "⟦data⟧",
          feeling: "⟦data⟧",
          why: "⟦data⟧",
        })),
      );
      apiClient.listDaySummaries.mockResolvedValue(
        summaries.map((summary) => ({
          ...summary,
          summary: "⟦data⟧",
          mood: "⟦data⟧",
          offered: "⟦data⟧",
        })),
      );
      apiClient.listSharedPhotos.mockResolvedValue(
        sharedPhotos.map((photo) => ({
          ...photo,
          description: "⟦data⟧",
          note: "⟦data⟧",
        })),
      );
    }

    async function expectOnlyCopyOnEveryTab(container: HTMLElement) {
      const user = userEvent.setup();
      await screen.findByRole("tabpanel");
      for (const tab of tabSlots) {
        await user.click(
          screen.getByRole("tab", { name: `⟦memories.tabs.${tab}⟧` }),
        );
        expect(wordsNotFromCopyOrDays(container)).toEqual([]);
      }
    }

    it("shows only Copy text on every tab with things remembered", async () => {
      markData();
      apiClient.getMe.mockResolvedValue({
        ...maya,
        changed_in_chat: { user_memory: "2026-11-03T09:00:00Z" },
      });

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      await expectOnlyCopyOnEveryTab(container);
    });

    it("shows only Copy text in a photo's box when it can't be shown", async () => {
      const user = userEvent.setup();
      markData();
      apiClient.getSharedPhotoImage.mockRejectedValue(new Error("down"));
      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      await user.click(
        await screen.findByRole("tab", { name: "⟦memories.tabs.photos⟧" }),
      );

      expect(
        (await screen.findAllByText("⟦memories.photos.photo_failed⟧")).length,
      ).toBe(2);
      expect(wordsNotFromCopyOrDays(container)).toEqual([]);
    });

    it("shows only Copy text on every tab with nothing remembered", async () => {
      apiClient.listMemoryGroups.mockResolvedValue([]);
      apiClient.getUserPortrait.mockResolvedValue(null);
      apiClient.listLifeThreads.mockResolvedValue([]);
      apiClient.listPatterns.mockResolvedValue([]);
      apiClient.listMoveOutcomes.mockResolvedValue([]);
      apiClient.listDaySummaries.mockResolvedValue([]);
      apiClient.listSharedPhotos.mockResolvedValue([]);
      apiClient.listKeptQuotes.mockResolvedValue([]);

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      await expectOnlyCopyOnEveryTab(container);
    });

    it("shows only Copy text while Memory is paused, with its note and button", async () => {
      markData();
      apiClient.getMe.mockResolvedValue({
        ...maya,
        user_memory_enabled: false,
      });

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      expect(
        await screen.findByRole("button", {
          name: "⟦memories.memory_off.turn_on⟧",
        }),
      ).toBeVisible();
      expect(screen.getByText("⟦memories.switch.paused⟧")).toBeVisible();
      expect(wordsNotFromCopy(container)).toEqual([]);
    });

    it("shows only Copy text when an Admin has Memory off", async () => {
      markData();
      apiClient.getMe.mockResolvedValue({
        ...maya,
        user_memory_enabled: false,
        user_memory_available: false,
      });

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      expect(
        await screen.findByText("⟦memories.switch.not_available⟧"),
      ).toBeVisible();
      expect(wordsNotFromCopy(container)).toEqual([]);
    });

    it("shows only Copy text while loading", () => {
      apiClient.listMemoryGroups.mockReturnValue(new Promise(() => {}));

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      expect(
        screen.getByRole("status", { name: "⟦memories.loading⟧" }),
      ).toBeInTheDocument();
      expect(wordsNotFromCopy(container)).toEqual([]);
    });

    it("shows only Copy text when the memories couldn't load", async () => {
      apiClient.listMemoryGroups.mockRejectedValue(new Error("down"));

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);

      expect(await screen.findByRole("alert")).toHaveTextContent(
        "⟦memories.load_failed.title⟧",
      );
      expect(
        screen.getByRole("button", { name: "⟦memories.load_failed.retry⟧" }),
      ).toBeVisible();
      expect(wordsNotFromCopy(container)).toEqual([]);
    });

    it("shows only Copy text when a change or a delete fails, and in the delete all dialog", async () => {
      const user = userEvent.setup();
      markData();
      apiClient.updatePreferences.mockRejectedValue(new Error("down"));
      apiClient.deleteMemoryItem.mockRejectedValue(new Error("down"));

      const { container } = renderWithQueries(<Memories copy={markedCopy()} />);
      await user.click(
        await screen.findByRole("switch", { name: "⟦memories.switch.label⟧" }),
      );
      await user.click(
        (
          await screen.findAllByRole("button", {
            name: "⟦memories.items.delete⟧",
          })
        )[0],
      );
      await screen.findByText("⟦memories.delete_failed⟧");
      await screen.findByText("⟦memories.switch.save_failed⟧");
      await user.click(
        screen.getByRole("button", {
          name: "⟦memories.items.delete_all.button⟧",
        }),
      );

      const dialog = within(screen.getByRole("alertdialog"));
      expect(
        dialog.getByText("⟦memories.items.delete_all.confirm_body_many⟧"),
      ).toBeVisible();
      expect(wordsNotFromCopy(container)).toEqual([]);
    });

    it("words the delete all dialog for one memory with one Memory Item", async () => {
      const user = userEvent.setup();
      apiClient.listMemoryGroups.mockResolvedValue([
        { category: "Life details", items: [groups[0].items[0]] },
      ]);
      renderWithQueries(<Memories copy={markedCopy()} />);

      await user.click(
        await screen.findByRole("button", {
          name: "⟦memories.items.delete_all.button⟧",
        }),
      );

      expect(
        within(screen.getByRole("alertdialog")).getByText(
          "⟦memories.items.delete_all.confirm_body_one⟧",
        ),
      ).toBeVisible();
    });

    it("words the delete all dialog for several memories with more than one", async () => {
      const user = userEvent.setup();
      renderWithQueries(<Memories copy={markedCopy()} />);

      await user.click(
        await screen.findByRole("button", {
          name: "⟦memories.items.delete_all.button⟧",
        }),
      );

      expect(
        within(screen.getByRole("alertdialog")).getByText(
          "⟦memories.items.delete_all.confirm_body_many⟧",
        ),
      ).toBeVisible();
    });
  });
});
