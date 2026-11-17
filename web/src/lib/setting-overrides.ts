import type {
  MoveOverride,
  NeedOverride,
  OverridableMove,
  OverridableNeed,
  OverrideChoices,
} from "@/lib/api-client";

/** The start of a Need override's key, `need:<id>`. */
export const needOverridePrefix = "need:";

/** The start of a Move override's key, `move:<id>`. */
export const moveOverridePrefix = "move:";

/** The Needs and Moves when a run started, to name its overrides by. */
export type NeedsAndMovesAtRunStart = {
  needs: OverridableNeed[];
  moves: OverridableMove[];
};

/**
 * Says whether a value holds each named field as text.
 *
 * @param value - The value.
 * @param names - The fields it must hold.
 * @returns True if it is an object with each field as text.
 */
function hasTextFields(value: unknown, names: string[]): boolean {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const fields = value as Record<string, unknown>;
  return names.every((name) => typeof fields[name] === "string");
}

/**
 * Says whether a value is a Need's details, as a Need override holds them.
 *
 * @param value - The value.
 * @returns True if it has a name, when it fits and how to reply as text.
 */
export function isNeedOverride(value: unknown): value is NeedOverride {
  return hasTextFields(value, ["name", "when_it_fits", "how_to_reply"]);
}

/**
 * Says whether a value is a Move's text, as a Move override holds it.
 *
 * @param value - The value.
 * @returns True if it has a name, when it fits and how to do it as text.
 */
export function isMoveOverride(value: unknown): value is MoveOverride {
  return hasTextFields(value, ["name", "when_it_fits", "how_to_do_it"]);
}

/**
 * Names an overridden setting as the settings pages do.
 *
 * @param key - The override's key.
 * @param choices - What a Variant can override, for setting labels and live
 *   names.
 * @param then - The Needs and Moves when the run started, whose names are
 *   used first; none for a new run.
 * @returns E.g. "Understanding thinking", "Need: Be heard" or "Move:
 *   Research"; the key when it can't be named.
 */
export function overrideLabel(
  key: string,
  choices: OverrideChoices | undefined,
  then: NeedsAndMovesAtRunStart = { needs: [], moves: [] },
): string {
  if (key.startsWith(needOverridePrefix)) {
    const need =
      then.needs.find((other) => other.key === key) ??
      choices?.needs.find((other) => other.key === key);
    return `Need: ${need?.name ?? "a Need deleted since"}`;
  }
  if (key.startsWith(moveOverridePrefix)) {
    const move =
      then.moves.find((other) => other.key === key) ??
      choices?.moves.find((other) => other.key === key);
    return `Move: ${move?.name ?? "a Move deleted since"}`;
  }
  return choices?.settings.find((setting) => setting.key === key)?.label ?? key;
}

/**
 * Writes a setting's value for reading.
 *
 * @param value - The value: text, a number, on/off, or a Need's or Move's
 *   text.
 * @returns E.g. "On", "1,200", the text, or a Need's or Move's three parts;
 *   "—" when there is none.
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
  if (isMoveOverride(value)) {
    return `${value.name}\nWhen it fits: ${value.when_it_fits}\nHow to do it: ${value.how_to_do_it}`;
  }
  return typeof value === "string" ? value : JSON.stringify(value);
}

/**
 * Says what settings a Variant runs with.
 *
 * @param changedCount - How many Setting Overrides it has.
 * @returns "live settings", or e.g. "live settings with 2 changed".
 */
export function describeVariantSettings(changedCount: number): string {
  return changedCount === 0
    ? "live settings"
    : `live settings with ${changedCount} changed`;
}
