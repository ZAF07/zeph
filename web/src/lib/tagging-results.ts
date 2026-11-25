import type {
  DroppedObservation,
  ExpectedObservation,
  KeptObservation,
  TaggingResult,
  UnclearStory,
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
 * Says how an unclear story ended, or was expected to end.
 *
 * @param patternType - The Pattern Type it is clear for; null while unclear.
 * @returns E.g. "Clear for CONF.AVOID.BELONG" or "Unclear".
 */
export function describeEnding(patternType: string | null): string {
  return patternType ? `Clear for ${patternType}` : "Unclear";
}

/**
 * Names what an unclear story is now, as a kept Observation is named.
 *
 * @param story - The unclear story after tagging.
 * @returns E.g. "CONF.AVOID.BELONG I2 · for", or its two Pattern Types
 *   with "unclear" while it stays unclear.
 */
export function describeUnclearNow(story: UnclearStory): string {
  return story.ended_clear_for
    ? `${[story.ended_clear_for, story.sign].filter(Boolean).join(" ")} · ${story.direction}`
    : `${story.pattern_types.join(" or ")} · ${story.direction} · unclear`;
}

/**
 * Says how a Tagging case's result differs from what was expected.
 *
 * @param result - What the case kept, dropped and expected, and how its
 *   unclear stories ended.
 * @returns The pill's label: "Passed", or e.g. "Failed · 1 not kept · 1
 *   not expected · 1 unclear story wrong", or "Failed · answer unreadable".
 */
export function taggingVerdict(result: TaggingResult): string {
  if (!result.answered) {
    return "Failed · answer unreadable";
  }
  const notKept = result.expected.filter((item) => !item.matched).length;
  const notExpected = result.kept.filter((item) => !item.expected).length;
  const unclearWrong = result.unclear.filter((item) => !item.matched).length;
  if (notKept === 0 && notExpected === 0 && unclearWrong === 0) {
    return "Passed";
  }
  return [
    "Failed",
    ...(notKept > 0 ? [`${notKept} not kept`] : []),
    ...(notExpected > 0 ? [`${notExpected} not expected`] : []),
    ...(unclearWrong > 0
      ? [
          `${unclearWrong} unclear ${unclearWrong === 1 ? "story" : "stories"} wrong`,
        ]
      : []),
  ].join(" · ");
}
