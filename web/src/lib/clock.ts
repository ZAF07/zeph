import { env } from "@/env";

/**
 * The moment design-fixture mode stands still at: Tuesday 17 Nov 2026,
 * 8:00 PM in Singapore, Alex's time zone, so the greeting reads "Good
 * evening" and it falls after every date drawn in `design/reference/`.
 */
export const DESIGN_FIXTURE_NOW = "2026-11-17T20:00:00+08:00";

/**
 * Tells the time, fixed in design-fixture mode so pages match the reference.
 *
 * @param designFixtures - Whether design-fixture mode is on.
 * @returns The current time, or the fixed design moment.
 */
export function currentTime(designFixtures = env.designFixtures): Date {
  return designFixtures ? new Date(DESIGN_FIXTURE_NOW) : new Date();
}
