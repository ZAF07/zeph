/** A time zone the User can pick. */
export type TimeZoneOption = {
  name: string;
  label: string;
};

/**
 * Says a time zone's current offset from GMT, e.g. "GMT+8".
 *
 * @param timeZone - The IANA time zone name.
 * @returns The offset.
 */
function gmtOffset(timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone,
    timeZoneName: "shortOffset",
  }).formatToParts(new Date());
  return parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT";
}

/**
 * Turns an IANA time zone name into a friendly label, e.g.
 * "Asia/Singapore" becomes "Singapore (GMT+8)".
 *
 * @param timeZone - The IANA time zone name.
 * @returns The label.
 */
export function timeZoneLabel(timeZone: string): string {
  const place = timeZone.split("/").slice(1).join(" / ") || timeZone;
  return `${place.replaceAll("_", " ")} (${gmtOffset(timeZone)})`;
}

/**
 * Lists every time zone the browser knows, plus any extra one that must be
 * offered, such as a saved value.
 *
 * @param extraTimeZone - A time zone to include even if the browser's list
 *   lacks it.
 * @returns The time zones, sorted by name.
 */
export function timeZoneOptions(
  extraTimeZone?: string | null,
): TimeZoneOption[] {
  const names = new Set(Intl.supportedValuesOf("timeZone"));
  if (extraTimeZone) {
    names.add(extraTimeZone);
  }
  return [...names]
    .sort()
    .map((name) => ({ name, label: timeZoneLabel(name) }));
}

/**
 * Reads the browser's time zone.
 *
 * @returns The IANA time zone name, e.g. "Asia/Singapore".
 */
export function timeZoneFromBrowser(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}
