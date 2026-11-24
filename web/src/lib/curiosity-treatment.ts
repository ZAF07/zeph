import type { CuriosityTreatment } from "@/lib/api-client";

/** The choices for how a Need treats Curiosities, in the order shown. */
export const curiosityTreatmentOptions: {
  value: CuriosityTreatment;
  label: string;
}[] = [
  { value: "ask_by_default", label: "Ask by default" },
  { value: "only_if_it_fits", label: "Only if it fits" },
  { value: "never", label: "Never" },
];

/** What a new Need starts with, and what an unknown choice reads as. */
export const defaultCuriosityTreatment: CuriosityTreatment = "only_if_it_fits";

/**
 * Names a choice for how a Need treats Curiosities.
 *
 * @param treatment - The choice.
 * @returns E.g. "Ask by default".
 */
export function curiosityTreatmentLabel(treatment: CuriosityTreatment): string {
  return (
    curiosityTreatmentOptions.find((option) => option.value === treatment)
      ?.label ?? treatment
  );
}

/**
 * Reads a choice picked in a select.
 *
 * @param value - The picked option's value.
 * @returns The choice; only if it fits, for a value that is none of them.
 */
export function toCuriosityTreatment(value: string): CuriosityTreatment {
  return (
    curiosityTreatmentOptions.find((option) => option.value === value)?.value ??
    defaultCuriosityTreatment
  );
}
