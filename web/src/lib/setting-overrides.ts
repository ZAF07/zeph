import type {
  NeedOverride,
  OverridableNeed,
  OverrideChoices,
} from "@/lib/api-client";

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
