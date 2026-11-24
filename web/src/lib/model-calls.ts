import type {
  CheckInShape,
  ModelStep,
  ReplyPlanShape,
  TaggingShape,
  TraceKind,
  UnderstandingShape,
} from "@/lib/api-client";

/** The steps Admins filter the Model Call Log by, in order, with labels. */
export const modelSteps: { id: ModelStep; label: string }[] = [
  { id: "safeguard", label: "Safeguard" },
  { id: "understanding", label: "Understanding" },
  { id: "reply_plan", label: "Reply Plan" },
  { id: "photo", label: "Photo" },
  { id: "reply", label: "Reply" },
  { id: "check_in", label: "Check-in" },
  { id: "conversation_end", label: "Conversation end" },
  { id: "life_threads", label: "Life Threads" },
  { id: "curiosities", label: "Curiosities" },
  { id: "move_outcomes", label: "Move Outcomes" },
  { id: "pattern_tagging", label: "Pattern tagging" },
  { id: "patterns", label: "Pattern keeping" },
  { id: "portrait", label: "User Portrait" },
  { id: "personal_stickers", label: "Personal Stickers" },
];

const traceKindLabels: Record<TraceKind, string> = {
  message: "Message",
  check_in: "Check-in",
  conversation_end: "Conversation end",
  portrait_rewrite: "Portrait rewrite",
};

/**
 * Names a step in plain words.
 *
 * @param step - The step.
 * @returns Its label, e.g. "Understanding".
 */
export function modelStepLabel(step: ModelStep): string {
  return modelSteps.find((option) => option.id === step)?.label ?? step;
}

/**
 * Names what a trace was for in plain words.
 *
 * @param kind - The trace's kind.
 * @returns Its label, e.g. "Check-in".
 */
export function traceKindLabel(kind: TraceKind): string {
  return traceKindLabels[kind];
}

const numberFormat = new Intl.NumberFormat("en");

/**
 * Writes the tokens a model call or trace took.
 *
 * @param tokensIn - Tokens the model read.
 * @param tokensOut - Tokens the model wrote.
 * @returns E.g. "1,200 in / 80 out".
 */
export function formatTokens(tokensIn: number, tokensOut: number): string {
  return `${numberFormat.format(tokensIn)} in / ${numberFormat.format(tokensOut)} out`;
}

/**
 * Writes how long something took, like "850 ms" or "2.4 s".
 *
 * @param milliseconds - The time taken.
 * @returns The time, in seconds from one second up.
 */
export function formatDuration(milliseconds: number): string {
  if (milliseconds < 1000) {
    return `${milliseconds} ms`;
  }
  return `${(milliseconds / 1000).toFixed(1)} s`;
}

/**
 * Lists a trace's steps once each, in the order they first ran, so a
 * retried step shows once with how many times it ran.
 *
 * @param steps - The trace's steps, one per call, in order.
 * @returns E.g. "Safeguard ×2 → Reply".
 */
export function describeSteps(steps: ModelStep[]): string {
  const counts = new Map<ModelStep, number>();
  for (const step of steps) {
    counts.set(step, (counts.get(step) ?? 0) + 1);
  }
  return [...counts]
    .map(([step, count]) =>
      count > 1 ? `${modelStepLabel(step)} ×${count}` : modelStepLabel(step),
    )
    .join(" → ");
}

/**
 * Lists the facts of a check on whether a reply brought up its Woven-in
 * Check-in, as labels and values.
 *
 * @param shape - The check's shape.
 * @returns E.g. "Check-in Kind: A follow-up", "Brought up: Yes".
 */
export function checkInShapeFacts(
  shape: CheckInShape,
): { label: string; value: string }[] {
  return [
    { label: "Check-in Kind", value: shape.kind },
    { label: "Brought up", value: shape.brought_up ? "Yes" : "No" },
  ];
}

/**
 * Lists the facts of a Pattern tagging call, as labels and values.
 *
 * @param shape - The call's shape.
 * @returns E.g. "Observations tagged: 3", "Dropped by code: 1".
 */
export function taggingShapeFacts(
  shape: TaggingShape,
): { label: string; value: string }[] {
  return [
    { label: "Observations tagged", value: String(shape.tagged) },
    { label: "Dropped by code", value: String(shape.dropped) },
  ];
}

const intensityLabels: Record<UnderstandingShape["intensity"], string> = {
  low: "Low",
  medium: "Medium",
  high: "Strong",
};

/**
 * Lists the facts of an Understanding's shape, as labels and values.
 *
 * @param shape - The Understanding's shape.
 * @returns E.g. "Mood intensity: Strong", "Cause known: Yes", "Struggling:
 * No", "Past look-ups: 1".
 */
export function understandingShapeFacts(
  shape: UnderstandingShape,
): { label: string; value: string }[] {
  return [
    { label: "Mood intensity", value: intensityLabels[shape.intensity] },
    { label: "Cause known", value: shape.cause_known ? "Yes" : "No" },
    { label: "Struggling", value: shape.struggling ? "Yes" : "No" },
    { label: "Past look-ups", value: String(shape.past_look_ups) },
  ];
}

/**
 * Says whether a Reply Plan built its Read on a Pattern and offered it.
 *
 * @param shape - The Reply Plan's shape.
 * @returns "Offered", "Used, not offered" or "None".
 */
export function describePatternUse(shape: ReplyPlanShape): string {
  if (shape.pattern_offered) {
    return "Offered";
  }
  return shape.pattern_used ? "Used, not offered" : "None";
}

/**
 * Lists a Reply Plan's facts about Curiosities, as labels and values.
 *
 * @param shape - The Reply Plan's shape.
 * @returns "Curiosities offered: 2" and "Curiosity asked: Yes"; nothing for
 * a trace saved before they were recorded.
 */
function curiosityFacts(
  shape: ReplyPlanShape,
): { label: string; value: string }[] {
  if (shape.curiosities_offered == null || shape.curiosity_asked == null) {
    return [];
  }
  return [
    { label: "Curiosities offered", value: String(shape.curiosities_offered) },
    { label: "Curiosity asked", value: shape.curiosity_asked ? "Yes" : "No" },
  ];
}

/**
 * Lists the facts of a Reply Plan's shape, as labels and values.
 *
 * @param shape - The Reply Plan's shape.
 * @returns E.g. "Need picked: Be heard", "Lead Move: Calm", "Threads brought
 * up: 2 (1 lead, 1 weave)", "Read formed: Yes", "Read said: No", "Pattern:
 * Used, not offered", "Check-in Kinds offered: 2", "Check-in Kind chosen:
 * None", "Curiosities offered: 2", "Curiosity asked: Yes".
 */
export function replyPlanShapeFacts(
  shape: ReplyPlanShape,
): { label: string; value: string }[] {
  const broughtUp = shape.threads_led_with + shape.threads_woven_in;
  return [
    { label: "Need picked", value: shape.need },
    { label: "Lead Move", value: shape.lead_move ?? "None" },
    { label: "Supporting Move", value: shape.support_move ?? "None" },
    { label: "Next Move", value: shape.next_move ?? "None" },
    { label: "Life Threads reminded", value: String(shape.threads_reminded) },
    {
      label: "Threads brought up",
      value:
        broughtUp > 0
          ? `${broughtUp} (${shape.threads_led_with} lead, ${shape.threads_woven_in} weave)`
          : "0",
    },
    { label: "Threads left alone", value: String(shape.threads_left_alone) },
    { label: "Threads held back", value: String(shape.threads_held_back) },
    { label: "Read formed", value: shape.read_formed ? "Yes" : "No" },
    { label: "Read said", value: shape.read_said ? "Yes" : "No" },
    { label: "Pattern", value: describePatternUse(shape) },
    {
      label: "Check-in Kinds offered",
      value: String(shape.check_in_kinds_offered),
    },
    { label: "Check-in Kind chosen", value: shape.check_in_kind ?? "None" },
    ...curiosityFacts(shape),
  ];
}
