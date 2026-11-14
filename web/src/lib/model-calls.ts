import type { ModelStep, TraceKind } from "@/lib/api-client";

/** The steps Admins filter the Model Call Log by, in order, with labels. */
export const modelSteps: { id: ModelStep; label: string }[] = [
  { id: "safeguard", label: "Safeguard" },
  { id: "understanding", label: "Understanding" },
  { id: "photo", label: "Photo" },
  { id: "reply", label: "Reply" },
  { id: "check_in", label: "Check-in" },
  { id: "conversation_end", label: "Conversation end" },
  { id: "life_threads", label: "Life Threads" },
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
