import type {
  CaseResult,
  NeedOverride,
  OverridableNeed,
  OverrideChoices,
} from "@/lib/api-client";
import { outcomeLabels } from "@/lib/evals";
import { formatDuration, formatTokens } from "@/lib/model-calls";

/** The start of a Need override's key, `need:<id>`. */
export const needOverridePrefix = "need:";

/**
 * Says whether a value is a Need's details, as a Need override holds them.
 *
 * @param value - The value.
 * @returns True if it has a name, when it fits and how to reply as text.
 */
export function isNeedOverride(value: unknown): value is NeedOverride {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const fields = value as Record<string, unknown>;
  return (
    typeof fields.name === "string" &&
    typeof fields.when_it_fits === "string" &&
    typeof fields.how_to_reply === "string"
  );
}

/**
 * Names an overridden setting as the settings pages do.
 *
 * @param key - The override's key.
 * @param choices - What a Variant can override, for setting labels.
 * @param needs - Needs to find a Need override's name in, such as those
 *   when the run started.
 * @returns E.g. "Understanding thinking" or "Need: Be heard"; the key when
 *   it can't be named.
 */
export function overrideLabel(
  key: string,
  choices: OverrideChoices | undefined,
  needs: OverridableNeed[],
): string {
  if (key.startsWith(needOverridePrefix)) {
    const need =
      needs.find((other) => other.key === key) ??
      choices?.needs.find((other) => other.key === key);
    return `Need: ${need?.name ?? "a Need deleted since"}`;
  }
  return choices?.settings.find((setting) => setting.key === key)?.label ?? key;
}

/**
 * Writes a setting's value for reading.
 *
 * @param value - The value: text, a number, on/off or a Need's details.
 * @returns E.g. "On", "1,200", the text, or a Need's three parts; "—" when
 *   there is none.
 */
export function describeSettingValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "On" : "Off";
  }
  if (typeof value === "number") {
    return value.toLocaleString("en");
  }
  if (isNeedOverride(value)) {
    return `${value.name}\nWhen it fits: ${value.when_it_fits}\nHow to reply: ${value.how_to_reply}`;
  }
  return typeof value === "string" ? value : JSON.stringify(value);
}

/**
 * Sorts a run's Case Results into the grid's cells, one per case and Variant.
 *
 * @param results - The run's Case Results.
 * @returns Each cell's tries in try order, by `cellKey`.
 */
export function resultsByCell(
  results: CaseResult[],
): Map<string, CaseResult[]> {
  const cells = new Map<string, CaseResult[]>();
  for (const result of results) {
    const key = cellKey(result.case_key, result.variant);
    cells.set(key, [...(cells.get(key) ?? []), result]);
  }
  for (const tries of cells.values()) {
    tries.sort((one, other) => one.try_number - other.try_number);
  }
  return cells;
}

/**
 * Names a grid cell.
 *
 * @param caseKey - The case's key.
 * @param letter - The Variant's letter.
 * @returns The cell's key.
 */
export function cellKey(caseKey: string, letter: string): string {
  return `${caseKey}\u0000${letter}`;
}

/**
 * Says how a cell's tries went, as a pill.
 *
 * @param tries - The tries finished so far.
 * @param repeats - How many tries the cell has in all.
 * @returns A single try's outcome; otherwise e.g. "2 of 3 passed", coloured
 *   as a fail once any try failed, as a pass once all passed.
 */
export function triesPill(
  tries: CaseResult[],
  repeats: number,
): { label: string; pill: string } {
  const [only] = tries;
  if (repeats === 1 && only !== undefined) {
    return outcomeLabels[only.outcome];
  }
  const passed = tries.filter((result) => result.outcome === "pass").length;
  const outcome = tries.some((result) => result.outcome === "fail")
    ? "fail"
    : passed === repeats
      ? "pass"
      : "error";
  return {
    label: `${passed} of ${repeats} passed`,
    pill: outcomeLabels[outcome].pill,
  };
}

/**
 * Writes the tokens and time a cell's tries used, added up.
 *
 * @param tries - The tries.
 * @returns E.g. "1,800 in / 80 out · 4.8 s".
 */
export function describeTriesUsage(tries: CaseResult[]): string {
  const tokensIn = tries.reduce((sum, result) => sum + result.tokens_in, 0);
  const tokensOut = tries.reduce((sum, result) => sum + result.tokens_out, 0);
  const time = tries.reduce((sum, result) => sum + result.duration_ms, 0);
  return `${formatTokens(tokensIn, tokensOut)} · ${formatDuration(time)}`;
}
