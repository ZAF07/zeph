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

/** Alex's two Patterns, as drawn in `Memories--tab-patterns.html`. */
const patterns: Pattern[] = [
  {
    id: "design-pattern-1",
    pattern:
      "Treats rest as something to be earned, and feels he is falling behind whenever he stops.",
    agreed_at: "2026-11-12T20:00:00+08:00",
    evidence: [
      {
        day: "2026-11-12",
        thread: "Pushing hard at work",
        line: "Worked through the weekend so that nobody could say he had slowed down.",
      },
      {
        day: "2026-11-09",
        thread: "The van idea",
        line: "Called a few months of travelling reckless before anyone else could.",
      },
      {
        day: "2026-11-02",
        thread: "Time with his father",
        line: "Felt guilty about taking an afternoon off to visit.",
      },
    ],
  },
  {
    id: "design-pattern-2",
    pattern: "Names the worst version of a plan first, before anyone else can.",
    agreed_at: "2026-11-09T20:00:00+08:00",
    evidence: [
      {
        day: "2026-11-09",
        thread: "The van idea",
        line: "Asked whether the trip was just an escape before saying what he hoped to find.",
      },
      {
        day: "2026-10-28",
        thread: "The new job",
        line: "Listed the ways the job could go wrong in the first week.",
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
