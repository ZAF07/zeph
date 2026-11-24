import type {
  ExcludedEvidence,
  PatternArea,
  PatternType,
  PatternTypeStatus,
  SignPart,
  SignStrength,
} from "@/lib/api-client";
import { formatDay } from "@/lib/dates";

/** What each area is called on the Pattern Catalog page. */
export const areaLabels: Record<PatternArea, string> = {
  conflict: "Conflict",
  approval: "Approval",
  control: "Control",
  achievement: "Achievement",
  relationships: "Relationships",
};

/** What each sign strength is called. */
export const strengthLabels: Record<SignStrength, string> = {
  weak: "Weak",
  moderate: "Moderate",
  strong: "Strong",
};

/** What each part a sign shows is called. */
export const partLabels: Record<SignPart, string> = {
  situation: "Situation",
  inside: "What goes on inside",
  behaviour: "Behaviour",
};

/** What happens to evidence under an exclusion, in plain words. */
export const evidenceLabels: Record<ExcludedEvidence, string> = {
  ignored: "Evidence ignored",
  counted_not_shared: "Counted, not shared",
};

/** What each review status is called. */
export const statusLabels: Record<PatternTypeStatus, string> = {
  draft: "Draft",
  approved: "Approved",
  archived: "Archived",
};

/**
 * Writes a Pattern Type as one line: its situation, what the person does
 * and what that gets them.
 *
 * @param patternType - The Pattern Type.
 * @returns The line, such as "Disagreement → Softens own view → To belong".
 */
export function describeSignature(patternType: PatternType): string {
  return [
    patternType.if_situation,
    patternType.then_behaviour,
    patternType.function,
  ].join(" → ");
}

/**
 * Says where a Pattern Type stands in review and what that means.
 *
 * @param patternType - The Pattern Type.
 * @returns The status line, with who approved it and on which calendar day
 *   once approved.
 */
export function describeStatus(patternType: PatternType): string {
  const approval =
    patternType.approved_by && patternType.approved_on
      ? ` by ${patternType.approved_by} on ${formatDay(patternType.approved_on, "UTC")}`
      : "";
  const label = statusLabels[patternType.status];
  if (patternType.status === "draft") {
    return `${label}. Gathers evidence, never shared.`;
  }
  if (patternType.status === "approved") {
    return `${label}${approval}. May be shared once ready.`;
  }
  return `${label}${approval ? `. Approved${approval}` : ""}. No longer used.`;
}
