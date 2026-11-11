import type { RiskType } from "@/lib/api-client";

/** Every risk type, in the order the Dashboard lists them, with its label. */
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
  return riskTypes.find((option) => option.id === riskType)?.label ?? riskType;
}
