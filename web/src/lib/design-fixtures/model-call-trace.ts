import type {
  ApiClient,
  ModelCall,
  ModelCallContent,
  ModelCallTraceDetails,
} from "@/lib/api-client";

const startedAt = "2026-11-19T21:14:00+08:00";

/**
 * Content an Admin's own call keeps. The trace is drawn with every Content
 * closed, so only the Reply Plan's matches what `AdminModelCallTrace.html`
 * draws opened; the others hold placeholders.
 *
 * @param instructions - What the model was told.
 * @param response - What it answered.
 * @returns The content.
 */
function content(instructions: string, response: string): ModelCallContent {
  return {
    instructions,
    history: [],
    tools_offered: [],
    tool_calls: [],
    response,
    reasoning: null,
  };
}

/**
 * A call as `AdminModelCallTrace.html` draws it, with no shapes unless given.
 *
 * @param call - The call's own fields.
 * @returns The call.
 */
function drawnCall(
  call: Pick<
    ModelCall,
    | "id"
    | "step"
    | "model"
    | "thinking"
    | "duration_ms"
    | "tokens_in"
    | "tokens_out"
    | "content"
  > &
    Partial<ModelCall>,
): ModelCall {
  return {
    started_at: startedAt,
    error: null,
    tools_called: [],
    understanding_shape: null,
    check_in_shape: null,
    tagging_shape: null,
    reply_plan_shape: null,
    ...call,
  };
}

/** The four calls drawn in `AdminModelCallTrace.html`, in order. */
const calls: ModelCall[] = [
  drawnCall({
    id: "call-safeguard",
    step: "safeguard",
    model: "deepseek-chat",
    thinking: false,
    tokens_in: 410,
    tokens_out: 6,
    duration_ms: 420,
    content: content("[THE SAFEGUARD PROMPT]", "none"),
  }),
  drawnCall({
    id: "call-understanding",
    step: "understanding",
    model: "deepseek-chat",
    thinking: false,
    tokens_in: 2180,
    tokens_out: 142,
    duration_ms: 1300,
    content: content("[THE UNDERSTANDING PROMPT]", "[THE UNDERSTANDING]"),
    understanding_shape: {
      intensity: "high",
      cause_known: true,
      struggling: false,
      past_look_ups: 1,
    },
  }),
  drawnCall({
    id: "call-reply-plan",
    step: "reply_plan",
    model: "deepseek-reasoner",
    thinking: true,
    tokens_in: 4960,
    tokens_out: 288,
    duration_ms: 3600,
    tools_called: ["past_day"],
    content: {
      ...content(
        "[THE OUTLOOK]\n[THE REPLY PLAN PROMPT]",
        "Where we are: venting, nearly spent\nRead: He is not tired from the work. He is tired from proving he deserves to stop.\nSay it now: no, he is still mid-vent\nNeed: Be heard",
      ),
      tool_calls: [
        {
          name: "past_day",
          arguments: { date: "2026-11-12" },
          result: "14 messages from 12 Nov",
        },
      ],
    },
    reply_plan_shape: {
      need: "Be heard",
      lead_move: "Reflect back",
      support_move: null,
      next_move: "Offer a view",
      threads_reminded: 5,
      threads_led_with: 1,
      threads_woven_in: 0,
      threads_left_alone: 3,
      threads_held_back: 1,
      read_formed: true,
      read_said: false,
      check_in_kinds_offered: 2,
      check_in_kind: null,
      pattern_used: true,
      pattern_offered: false,
    },
  }),
  drawnCall({
    id: "call-reply",
    step: "reply",
    model: "deepseek-chat",
    thinking: false,
    tokens_in: 1870,
    tokens_out: 176,
    duration_ms: 1500,
    content: content("[THE VOICE]\n[THE REPLY PROMPT]", "[THE REPLY]"),
  }),
];

/** The trace drawn in `AdminModelCallTrace.html`: a Message for Zaf, an Admin. */
const designTrace: ModelCallTraceDetails = {
  trace_id: "design-trace",
  kind: "message",
  user_id: "user-zaf",
  user_name: "Zaf",
  user_email: null,
  started_at: startedAt,
  steps: calls.map((call) => call.step),
  tokens_in: 9420,
  tokens_out: 612,
  duration_ms: 6800,
  error_count: 0,
  has_content: true,
  calls,
};

/**
 * Design fixtures for the AdminModelCallTrace reference page. Values come
 * only from that reference file.
 */
export const modelCallTraceFixtures: Partial<ApiClient> = {
  getModelCallTrace: () => Promise.resolve(designTrace),
};
