import type {
  ApiClient,
  DaySummary,
  LifeThread,
  MemoryGroup,
  MoveOutcome,
  KeptQuote,
  Pattern,
  SharedPhoto,
  UserPortrait,
} from "@/lib/api-client";

/** Alex's Memory Items, as drawn in `Memories.html` and `M-Memories.html`. */
const memoryGroups: MemoryGroup[] = [
  {
    category: "Goals",
    items: [
      {
        id: "design-memory-goal-1",
        content: "Rest without feeling I am falling behind",
        source: "conversation",
        created_at: "2026-11-12T21:00:00+08:00",
        updated_at: "2026-11-12T21:00:00+08:00",
      },
      {
        id: "design-memory-goal-2",
        content: "Decide about travelling in a van for a while",
        source: "conversation",
        created_at: "2026-11-09T20:00:00+08:00",
        updated_at: "2026-11-09T20:00:00+08:00",
      },
    ],
  },
  {
    category: "Relationships",
    items: [
      {
        id: "design-memory-relationship-1",
        content: "Wants more patience with his father",
        source: "conversation",
        created_at: "2026-11-02T20:00:00+08:00",
        updated_at: "2026-11-02T20:00:00+08:00",
      },
    ],
  },
  {
    category: "Challenges",
    items: [
      {
        id: "design-memory-challenge-1",
        content: "Afraid that resting means losing ground",
        source: "conversation",
        created_at: "2026-11-12T21:00:00+08:00",
        updated_at: "2026-11-12T21:00:00+08:00",
      },
      {
        id: "design-memory-challenge-2",
        content: "Has been running on autopilot since starting a new job",
        source: "onboarding",
        created_at: "2026-10-28T20:00:00+08:00",
        updated_at: "2026-10-28T20:00:00+08:00",
      },
    ],
  },
];

/** Alex's User Portrait, as drawn in `Memories--tab-about.html`. */
const portrait: UserPortrait = {
  text: "Alex works hard and measures himself by momentum, which makes rest feel like a risk. He is weighing a bigger change and wants to be sure it is a choice and not an escape. He responds well to direct questions.",
  updated_at: "2026-11-12T22:00:00+08:00",
};

/** Alex's Life Threads, as drawn in `Memories--tab-threads.html`. */
const lifeThreads: LifeThread[] = [
  {
    id: "design-thread-1",
    title: "The van idea",
    story:
      "Thinking about moving into a van and travelling for a while. Excited, and unsure whether it is an escape.",
    is_open: true,
    updated_at: "2026-11-12T22:00:00+08:00",
  },
  {
    id: "design-thread-2",
    title: "Performance review",
    story: "Prepared carefully and it went better than feared.",
    is_open: false,
    updated_at: "2026-11-07T20:00:00+08:00",
  },
];

/** Alex's four Patterns, as drawn in `Memories--tab-patterns.html`. */
const patterns: Pattern[] = [
  {
    id: "design-pattern-1",
    state: "shared",
    pattern:
      "You seem to treat rest as something to be earned, and feel you are falling behind whenever you stop.",
    where_it_shows: [],
    told_at: "2026-11-12T20:00:00+08:00",
    quote_groups: [
      {
        life_thread: "Pushing hard at work",
        quotes: [
          {
            quote: "If I stop now, everyone will see I can't keep up.",
            day: "2026-11-12",
          },
          {
            quote:
              "I worked the whole weekend so nobody could say I'd slowed down.",
            day: "2026-11-08",
          },
        ],
      },
      {
        life_thread: "Time with his father",
        quotes: [
          {
            quote: "I felt guilty the whole afternoon I took off.",
            day: "2026-11-02",
          },
        ],
      },
    ],
    predictions: [
      {
        wording:
          "Next time you take an evening off, notice whether you start listing what you should be doing instead.",
        made_at: "2026-11-12T20:00:00+08:00",
        outcome: null,
      },
    ],
  },
  {
    id: "design-pattern-2",
    state: "confirmed",
    pattern:
      "You seem to name the worst version of a plan first, before anyone else can.",
    where_it_shows: [
      {
        condition: "relationship",
        shows_with: ["family", "friend"],
        not_with: ["colleague"],
      },
    ],
    told_at: "2026-11-01T20:00:00+08:00",
    quote_groups: [
      {
        life_thread: "The van idea",
        quotes: [
          {
            quote: "It's probably just me running away, I know.",
            day: "2026-11-09",
          },
        ],
      },
      {
        life_thread: "The new job",
        quotes: [
          {
            quote: "I'll tell you now, I'm going to mess up the first week.",
            day: "2026-10-28",
          },
        ],
      },
    ],
    predictions: [
      {
        wording:
          "Next time someone asks about the van trip, notice whether you call it reckless before they can.",
        made_at: "2026-11-06T20:00:00+08:00",
        outcome: "came_true",
      },
      {
        wording:
          "Next time you share a plan with your father, notice whether you start with what could go wrong.",
        made_at: "2026-11-01T20:00:00+08:00",
        outcome: "came_true",
      },
    ],
  },
  {
    id: "design-pattern-3",
    state: "contested",
    pattern:
      "You seem to protect closeness by keeping disagreements small, even when they matter to you.",
    where_it_shows: [],
    told_at: "2026-11-05T20:00:00+08:00",
    quote_groups: [
      {
        life_thread: "Time with his father",
        quotes: [
          {
            quote: "I just said it was fine, it wasn't worth the argument.",
            day: "2026-11-04",
          },
        ],
      },
      {
        life_thread: null,
        quotes: [
          { quote: "I went along with it, like always.", day: "2026-11-03" },
        ],
      },
    ],
    predictions: [
      {
        wording:
          "Next time your father asks for something you'd rather not do, notice whether you say yes before you've decided.",
        made_at: "2026-11-05T20:00:00+08:00",
        outcome: null,
      },
    ],
  },
  {
    id: "design-pattern-4",
    state: "closed",
    pattern:
      "You seem to check that things are still alright with people after a disagreement.",
    where_it_shows: [],
    told_at: "2026-10-20T20:00:00+08:00",
    quote_groups: [
      {
        life_thread: "The new job",
        quotes: [
          {
            quote: "I messaged her twice to check we were okay.",
            day: "2026-10-18",
          },
        ],
      },
    ],
    predictions: [
      {
        wording:
          "Next time you disagree with someone at work, notice whether you message them afterwards to check.",
        made_at: "2026-10-20T20:00:00+08:00",
        outcome: "did_not",
      },
    ],
  },
];

/** Alex's kept quotes, as drawn in `Memories--tab-quotes.html`. */
const keptQuotes: KeptQuote[] = [
  {
    id: "design-quote-1",
    quote: "If I stop now, everyone will see I can't keep up.",
    context: "Talking about working through the weekend.",
    day: "2026-11-12",
  },
  {
    id: "design-quote-2",
    quote: "It's probably just me running away again.",
    context: "Talking about the van trip he has been planning.",
    day: "2026-11-09",
  },
  {
    id: "design-quote-3",
    quote: "I felt like I hadn't earned the afternoon off.",
    context: "After visiting his father on a weekday.",
    day: "2026-11-02",
  },
];

/** Alex's Move Outcomes, as drawn in `Memories--tab-helps.html`. */
const moveOutcomes: MoveOutcome[] = [
  {
    id: "design-outcome-1",
    move: "Ask a question",
    role: "lead",
    situation: "Worried about a review the day before",
    feeling: "Anxious, restless",
    result: "helped",
    why: "Separating what he controls from what he doesn't calmed him down",
    made_at: "2026-11-11T20:00:00+08:00",
  },
];

/** Alex's Day Summaries, as drawn in `Memories--tab-summaries.html`. */
const summaries: DaySummary[] = [
  {
    id: "design-summary-1",
    summary:
      "Talked about being tired but afraid to slow down. Traced the fear to self-trust more than productivity.",
    mood: "Tired, thoughtful",
    offered: "A question about what rest would look like as part of progress",
    day: "2026-11-12",
    written_at: "2026-11-12T22:00:00+08:00",
  },
];

/** Alex's Shared Photos, as drawn in `Memories--tab-photos.html`. */
const sharedPhotos: SharedPhoto[] = [
  {
    id: "design-photo-1",
    description: "A camper van parked beside a lake at dusk.",
    note: "Kept because it shows the kind of life he is thinking about.",
    caption: "",
    sent_at: "2026-11-09T19:00:00+08:00",
  },
];

/**
 * Design fixtures for the Memories reference pages. Values come only from
 * those reference files. Only the issue building this area fills it. The
 * reference draws the photo as its dashed "Photo" box, so the photo's
 * image never finishes loading.
 */
export const memoriesFixtures: Partial<ApiClient> = {
  listMemoryGroups: async () => memoryGroups,
  getUserPortrait: async () => portrait,
  listLifeThreads: async () => lifeThreads,
  listPatterns: async () => patterns,
  listKeptQuotes: async () => keptQuotes,
  listMoveOutcomes: async () => moveOutcomes,
  listDaySummaries: async () => summaries,
  listSharedPhotos: async () => sharedPhotos,
  getSharedPhotoImage: () => new Promise<Blob>(() => {}),
};
