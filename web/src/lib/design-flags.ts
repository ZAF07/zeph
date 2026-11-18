import { env } from "@/env";

/** A `?design=` flag that forces a state for the pixel test (ADR 0018). */
export type DesignFlag =
  "all-steps" | "menu-folded" | "menu-open" | "all-folded";

/**
 * Says whether the address asks for a design state. Flags are honoured only
 * in design-fixture mode; otherwise they are ignored.
 *
 * @param searchParams - The page's query string.
 * @param flag - The state to look for.
 * @param designFixtures - Whether design-fixture mode is on.
 * @returns True when fixture mode is on and `?design=<flag>` is set.
 */
export function hasDesignFlag(
  searchParams: URLSearchParams | null,
  flag: DesignFlag,
  designFixtures = env.designFixtures,
): boolean {
  return designFixtures && searchParams?.get("design") === flag;
}
