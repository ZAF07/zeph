import type {
  CaseCheck,
  CaseOutcome,
  EvalName,
  EvalRunState,
} from "@/lib/api-client";

/** Each Eval's name on screen and what it checks, in the order shown. */
export const evalDetails: Record<EvalName, { label: string; checks: string }> =
  {
    safeguard: {
      label: "Safeguard",
      checks: "Every real crisis is caught; false alarms are listed.",
    },
    persona: {
      label: "Persona",
      checks: "The Judge checks Zeph’s replies against the Persona rules.",
    },
    knowledge: {
      label: "Knowledge",
      checks:
        "After each change to a Knowledge Document, replies use the newest version.",
    },
    settings: {
      label: "Settings",
      checks: "Asking in chat changes exactly the right setting, or none.",
    },
    photo_descriptions: {
      label: "Photo descriptions",
      checks: "A photo’s description leaves out card numbers and passwords.",
    },
    understanding: {
      label: "Understanding",
      checks:
        "Each Message’s Understanding reads it right, and its Reply Plan picks the right Read, Need, Moves, Life Threads, Curiosities and Knowledge. Each check names its step.",
    },
    move_outcome: {
      label: "Move Outcome",
      checks:
        "A finished Conversation leaves the right Move Outcomes, with fair reasons that don’t judge the User.",
    },
    day_summary: {
      label: "Day Summary",
      checks:
        "Writes a Day Summary from a made-up day with the live memory processing prompt. The Judge then answers each question from the Summary alone, and the case passes only if every answer matches.",
    },
  };

/** Every Eval, in the order shown. */
export const evalOrder = Object.keys(evalDetails) as EvalName[];

/** Each run state's label and pill look: cream when finished, danger when it
 * ended early, outlined otherwise. */
export const runStateLabels: Record<
  EvalRunState,
  { label: string; pill: string }
> = {
  queued: { label: "Queued", pill: "border border-line-strong text-soft" },
  running: { label: "Running", pill: "border border-line-strong text-soft" },
  finished: { label: "Finished", pill: "bg-cream text-ink" },
  cancelled: {
    label: "Cancelled",
    pill: "border border-line-strong text-soft",
  },
  stopped_over_limit: {
    label: "Stopped over limit",
    pill: "border border-danger text-danger",
  },
  interrupted: {
    label: "Interrupted",
    pill: "border border-danger text-danger",
  },
};

/**
 * Each outcome's label and pill look: cream for a pass, danger for a fail,
 * outlined for an error, which doesn't count as a fail.
 */
export const outcomeLabels: Record<
  CaseOutcome,
  { label: string; pill: string }
> = {
  pass: { label: "Pass", pill: "bg-cream text-ink" },
  fail: { label: "Fail", pill: "border border-danger text-danger" },
  error: { label: "Error", pill: "border border-line-strong text-soft" },
};

/**
 * Writes a count with its noun, singular for one.
 *
 * @param count - How many.
 * @param noun - The noun for one, e.g. "case".
 * @returns E.g. "1 case" or "3 cases".
 */
export function countOf(count: number, noun: string): string {
  return `${count} ${count === 1 ? noun : `${noun}s`}`;
}

/**
 * Says whether a run may still change, so its page keeps checking.
 *
 * @param state - The run's state.
 * @returns True while it is Queued or Running.
 */
export function isRunGoing(state: EvalRunState): boolean {
  return state === "queued" || state === "running";
}

/**
 * Lists a run's Evals by name.
 *
 * @param evals - The run's Evals.
 * @returns E.g. "Safeguard, Persona".
 */
export function describeEvals(evals: EvalName[]): string {
  return evals.map((name) => evalDetails[name].label).join(", ");
}

/**
 * Writes how many cases passed, failed and errored.
 *
 * @param totals - The counts.
 * @returns E.g. "3 passed · 1 failed · 1 error"; errors only when there are
 *   some.
 */
export function describeTotals(totals: {
  passed: number;
  failed: number;
  errored: number;
}): string {
  const parts = [`${totals.passed} passed`, `${totals.failed} failed`];
  if (totals.errored > 0) {
    parts.push(countOf(totals.errored, "error"));
  }
  return parts.join(" · ");
}

/**
 * Splits a case's checks by the part of the case they check, such as the
 * Message in an Understanding case, keeping their order.
 *
 * @param checks - The case's checks.
 * @returns One group per part; a case with one part has one group named "".
 */
export function groupChecks(
  checks: CaseCheck[],
): { group: string; checks: CaseCheck[] }[] {
  const groups: { group: string; checks: CaseCheck[] }[] = [];
  for (const check of checks) {
    const last = groups.at(-1);
    if (last !== undefined && last.group === check.group) {
      last.checks.push(check);
    } else {
      groups.push({ group: check.group, checks: [check] });
    }
  }
  return groups;
}

/**
 * Reads an Eval's name from a page address.
 *
 * @param value - The address part, e.g. "persona".
 * @returns The Eval, or null if no Eval has that name.
 */
export function toEvalName(value: string): EvalName | null {
  return evalOrder.find((name) => name === value) ?? null;
}

/**
 * Writes an amount in SGD, with more decimals for amounts under a dollar so
 * a small run doesn't read as free.
 *
 * @param sgd - The amount.
 * @returns E.g. "S$1.24" or "S$0.0043".
 */
export function formatSgd(sgd: number): string {
  return `S$${sgd.toFixed(sgd >= 1 || sgd === 0 ? 2 : 4)}`;
}

/**
 * Writes what some tokens cost, naming the models with no Model Price.
 *
 * @param cost - `cost_sgd` and `unpriced_models`.
 * @returns E.g. "S$0.42", or "S$0.42 + deepseek-x (no price set)".
 */
export function describeCost(cost: {
  cost_sgd: number;
  unpriced_models: string[];
}): string {
  if (cost.unpriced_models.length === 0) {
    return formatSgd(cost.cost_sgd);
  }
  const unpriced = `${cost.unpriced_models.join(", ")} (no price set)`;
  return cost.cost_sgd > 0
    ? `${formatSgd(cost.cost_sgd)} + ${unpriced}`
    : unpriced;
}

/**
 * The address of one Eval's list of cases.
 *
 * @param evalName - The Eval.
 * @returns The address.
 */
export function evalCasesHref(evalName: EvalName): string {
  return `/admin/evals/cases/${evalName}`;
}

/**
 * The address of an Eval Case's editor.
 *
 * @param evalCase - The case's Eval and key.
 * @returns The address.
 */
export function evalCaseEditHref(evalCase: {
  eval: EvalName;
  key: string;
}): string {
  return `${evalCasesHref(evalCase.eval)}/edit/${evalCase.key}`;
}
