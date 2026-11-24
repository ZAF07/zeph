import type {
  DroppedObservation,
  ExpectedObservation,
  KeptObservation,
  TaggingResult,
} from "@/lib/api-client";

/**
 * Names an expected Observation as the Case Result's checks do.
 *
 * @param expected - The Observation expected.
 * @returns E.g. "CONF.AVOID.BELONG · for · unclear".
 */
export function describeExpected(expected: ExpectedObservation): string {
  return [
    expected.pattern_type,
    expected.direction,
    ...(expected.unclear ? ["unclear"] : []),
    ...(expected.situational ? ["situational"] : []),
  ].join(" · ");
}

/**
 * Names a kept Observation by its Pattern Types, sign and how it counts.
 *
 * @param kept - The kept Observation.
 * @returns E.g. "CONF.AVOID.BELONG I2 · for · situational", or with two
 *   Pattern Types "CONF.AVOID.BELONG or ACH.WORTH.PERF I2 · for · unclear".
 */
export function describeKept(kept: KeptObservation): string {
  return [
    `${kept.pattern_types.join(" or ")} ${kept.sign}`,
    kept.direction,
    ...(kept.unclear ? ["unclear"] : []),
    ...(kept.situational ? ["situational"] : []),
  ].join(" · ");
}

/**
 * Writes a dropped entry as the tagging model wrote it.
 *
 * @param dropped - The dropped entry.
 * @returns E.g. "CONF.AVOID.BELONG I5 · for"; "Nothing readable" when it
 *   named nothing.
 */
export function describeDropped(dropped: DroppedObservation): string {
  const parts = [
    [dropped.pattern_types.join(" or "), dropped.sign]
      .filter(Boolean)
      .join(" "),
    dropped.direction,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "Nothing readable";
}

/**
 * Says how a Tagging case's result differs from what was expected.
 *
 * @param result - What the case kept, dropped and expected.
 * @returns The pill's label: "Passed", or e.g. "Failed · 1 not kept · 1
 *   not expected", or "Failed · answer unreadable".
 */
export function taggingVerdict(result: TaggingResult): string {
  if (!result.answered) {
    return "Failed · answer unreadable";
  }
  const notKept = result.expected.filter((item) => !item.matched).length;
  const notExpected = result.kept.filter((item) => !item.expected).length;
  if (notKept === 0 && notExpected === 0) {
    return "Passed";
  }
  return [
    "Failed",
    ...(notKept > 0 ? [`${notKept} not kept`] : []),
    ...(notExpected > 0 ? [`${notExpected} not expected`] : []),
  ].join(" · ");
}
