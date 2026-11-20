import type {
  AdminSetting,
  AdminSettings,
  ApiClient,
  CoreServices,
} from "@/lib/api-client";

/** The Persona text drawn in `AdminPersona.html`'s editor. */
const persona = `You are Zeph, a companion for reflection.

Voice
Warm, plain and unhurried. Short messages. One question at a time.

Values
Honesty over comfort. Disagree when it helps. Never flatter.

Boundaries
You are an AI. You are not a therapist and you say so when it matters.`;

/**
 * The settings drawn on the form template: last saved 12 Nov, 9:14 PM by
 * Zaf, with the Voice editor's hint. The Ignore Threshold is 3, as the
 * Check-in log's paused row says.
 */
const adminSettings: AdminSettings = {
  persona: {
    hint: "How Zeph speaks: its tone, values and boundaries. The Reply reads this before every message, and so does a Check-in sent on its own.",
    value: persona,
    updated_at: "2026-11-12T21:14:00+08:00",
    updated_by: "Zaf",
  },
  check_in_ignore_threshold: {
    hint: "Unanswered Check-ins in a row before the scheduler pauses a User’s Check-ins and asks once about fewer.",
    value: 3,
    updated_at: "2026-11-12T21:14:00+08:00",
    updated_by: "Zaf",
  },
};

const modelHint =
  "Which model this step calls. A larger model is slower and costs more per Message.";
const thinkingHint =
  "Lets the model reason before it answers. Slower, and better on steps that decide.";
const startingValue = "2026-11-01T00:00:00+08:00";

/**
 * A setting as `AdminPrompts.html` draws it.
 *
 * @param value - The setting's value.
 * @param hint - The hint drawn with it.
 * @param savedByZafAt - When Zaf last saved it; the starting value if not given.
 * @returns The setting.
 */
function drawnSetting(
  value: AdminSetting["value"],
  hint: string,
  savedByZafAt?: string,
): AdminSetting {
  return {
    hint,
    value,
    updated_at: savedByZafAt ?? startingValue,
    updated_by: savedByZafAt ? "Zaf" : null,
  };
}

/** The prompts, models and thinking switches drawn in `AdminPrompts.html`. */
const promptSettings: AdminSettings = {
  understanding_prompt: drawnSetting(
    "Read the Message. Say what the User said and what they mean.\nSplit feelings and wants into said, read and unclear.\nDo not choose how to reply.",
    "What the Understanding is told to read. It runs first on every Message, and its answer goes to the Reply Plan.",
    "2026-11-18T16:02:00+08:00",
  ),
  understanding_model: drawnSetting("deepseek-chat", modelHint),
  understanding_thinking: drawnSetting(false, thinkingHint),
  reply_plan_prompt: drawnSetting(
    "You are given the Understanding, what Zeph remembers, and the Outlook.\nForm a Read of what is really going on. Say it only when there is room,\nit adds something, and it has not been said in this Conversation.",
    "How the Reply Plan weighs what a reply could do. It runs after the Understanding, and the Reply follows what it picks.",
  ),
  reply_plan_model: drawnSetting("deepseek-reasoner", modelHint),
  reply_plan_thinking: drawnSetting(true, thinkingHint),
  response_prompt: drawnSetting(
    "Answer a direct question first. Keep it short.\nFollow the plan. Never state a Read as fact.",
    "How the Reply writes. It runs last on every Message, after the voice and the Reply Plan’s guidance.",
    "2026-11-12T21:14:00+08:00",
  ),
  response_model: drawnSetting("deepseek-chat", modelHint),
  response_thinking: drawnSetting(false, thinkingHint),
  pattern_keeping_prompt: drawnSetting(
    "Start a suspected Pattern only when the same way of acting\nshows in two or more Threads. Confirm or close one from how\nthe User took a view Zeph offered.",
    "What counts as a Pattern. It runs once a Conversation ends, after Life Threads are kept.",
  ),
  pattern_keeping_model: drawnSetting("deepseek-reasoner", modelHint),
  pattern_keeping_thinking: drawnSetting(true, thinkingHint),
};

/** The four core services drawn in `AdminPrompts.html`, in its order. */
const coreServices: CoreServices = {
  services: [
    {
      name: "Understanding",
      runs_when: "Every Message · first",
      description:
        "Reads each Message: what the User said and means, how they feel, and what they want. It reads only and decides nothing.",
      prompt_key: "understanding_prompt",
      model_key: "understanding_model",
      thinking_key: "understanding_thinking",
      extra_prompts: [],
      extra_prompt_groups: [],
    },
    {
      name: "Reply Plan",
      runs_when: "Every Message · after the Understanding",
      description:
        "Decides what the reply should do: the Need, the Moves, which Threads to bring up, whether a Check-in fits, and Zeph’s Read.",
      prompt_key: "reply_plan_prompt",
      model_key: "reply_plan_model",
      thinking_key: "reply_plan_thinking",
      extra_prompts: [],
      extra_prompt_groups: [{ name: "Fallback wording", prompts: [] }],
    },
    {
      name: "Reply",
      runs_when: "Every Message · last",
      description:
        "Writes the message the User receives, in Zeph’s voice, following the Reply Plan.",
      prompt_key: "response_prompt",
      model_key: "response_model",
      thinking_key: "response_thinking",
      extra_prompts: [],
      extra_prompt_groups: [],
    },
    {
      name: "Pattern keeping",
      runs_when: "Conversation end · after Life Threads",
      description:
        "Looks across Life Threads for the same way of thinking, feeling or acting, and keeps it as a Pattern.",
      prompt_key: "pattern_keeping_prompt",
      model_key: "pattern_keeping_model",
      thinking_key: "pattern_keeping_thinking",
      extra_prompts: [],
      extra_prompt_groups: [],
    },
  ],
  model_choices: ["deepseek-chat", "deepseek-reasoner"],
};

/**
 * Design fixtures for the AdminPersona (the form template) and
 * AdminPrompts reference pages. Values come only from those reference files. Only the issue
 * building this area fills it.
 */
export const adminFormsFixtures: Partial<ApiClient> = {
  getAdminSettings: () =>
    Promise.resolve({ ...adminSettings, ...promptSettings }),
  getCoreServices: () => Promise.resolve(coreServices),
};
