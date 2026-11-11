import type { RiskType } from "@/lib/api-client";

/** The risk types Admins filter by, in order, with their labels. */
export const riskTypes: { id: RiskType; label: string }[] = [
  { id: "suicide_or_self_harm", label: "Suicide / self-harm" },
  { id: "danger_to_others", label: "Danger to others" },
  { id: "abuse", label: "Abuse" },
  { id: "medical_emergency", label: "Medical emergency" },
];

/**
 * Names a risk type in plain words.
 *
 * @param riskType - The risk type.
 * @returns Its label, e.g. "Suicide / self-harm".
 */
export function riskTypeLabel(riskType: RiskType): string {
  if (riskType === "unclear") {
    return "Unclear answer";
  }
  return riskTypes.find((option) => option.id === riskType)?.label ?? riskType;
}
