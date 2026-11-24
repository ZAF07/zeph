import {
  ApiError,
  type PatternTypeChoice,
  type ThoughtExperiment,
  type ThoughtExperimentInput,
  type ThoughtExperimentSensitivity,
} from "@/lib/api-client";

/** The sensitivities to choose from, least sensitive first. */
export const SENSITIVITY_OPTIONS: {
  value: ThoughtExperimentSensitivity;
  label: string;
}[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

/** What a card says when a save fails for any reason but leading wording. */
export const SAVE_FAILED_TEXT =
  "Couldn’t save the Thought Experiment. Please try again.";

/** A new Thought Experiment before the Admin fills it in. */
export const EMPTY_THOUGHT_EXPERIMENT: ThoughtExperimentInput = {
  wording: "",
  pattern_type_id: "",
  other_pattern_type_id: "",
  sensitivity: "low",
  starter: false,
  on: true,
};

/**
 * Takes what an Admin can set from a saved Thought Experiment.
 *
 * @param thoughtExperiment - The Thought Experiment as saved.
 * @returns Its wording, Pattern Types, sensitivity, starter flag and on/off.
 */
export function thoughtExperimentInputOf(
  thoughtExperiment: ThoughtExperimentInput,
): ThoughtExperimentInput {
  return {
    wording: thoughtExperiment.wording,
    pattern_type_id: thoughtExperiment.pattern_type_id,
    other_pattern_type_id: thoughtExperiment.other_pattern_type_id,
    sensitivity: thoughtExperiment.sensitivity,
    starter: thoughtExperiment.starter,
    on: thoughtExperiment.on,
  };
}

/**
 * Says whether a draft differs from the saved Thought Experiment.
 *
 * @param draft - The Thought Experiment as edited.
 * @param saved - The Thought Experiment as saved.
 * @returns True when any field changed.
 */
export function isThoughtExperimentChanged(
  draft: ThoughtExperimentInput,
  saved: ThoughtExperiment,
): boolean {
  const before = thoughtExperimentInputOf(saved);
  return (Object.keys(before) as (keyof ThoughtExperimentInput)[]).some(
    (key) => draft[key] !== before[key],
  );
}

/**
 * Says whether a draft can be saved: it has wording and two different
 * Pattern Types.
 *
 * @param draft - The Thought Experiment as edited.
 * @returns True when it is complete.
 */
export function isThoughtExperimentComplete(
  draft: ThoughtExperimentInput,
): boolean {
  return (
    draft.wording.trim() !== "" &&
    draft.pattern_type_id !== "" &&
    draft.other_pattern_type_id !== "" &&
    draft.pattern_type_id !== draft.other_pattern_type_id
  );
}

/**
 * Reads the leading phrases from a save the backend refused for its wording.
 *
 * @param failure - What the save threw.
 * @returns One line per leading phrase; null when it was refused for
 *   another reason, or not refused.
 */
export function leadingFlagsOf(failure: unknown): string[] | null {
  if (!(failure instanceof ApiError) || failure.status !== 422) {
    return null;
  }
  const leading = failure.fields.leading;
  return leading ? leading.split("\n") : null;
}

/**
 * Names the two Pattern Types a Thought Experiment tells apart.
 *
 * @param thoughtExperiment - The Thought Experiment.
 * @returns Their IDs, e.g. "CONF.AVOID.BELONG or ACH.WORTH.PERF".
 */
export function pairTitle(thoughtExperiment: ThoughtExperimentInput): string {
  return `${thoughtExperiment.pattern_type_id} or ${thoughtExperiment.other_pattern_type_id}`;
}

/**
 * Builds the choices for a Pattern Type select, by ID, keeping one already
 * named even if the catalog no longer has it.
 *
 * @param choices - The catalog's Pattern Types.
 * @param current - The Pattern Type chosen now; "" for none.
 * @returns The options, with "Choose one" first when none is chosen.
 */
export function patternTypeOptions(
  choices: PatternTypeChoice[],
  current: string,
): { value: string; label: string }[] {
  const options = choices.map((choice) => ({
    value: choice.id,
    label: choice.id,
  }));
  if (current === "") {
    return [{ value: "", label: "Choose one" }, ...options];
  }
  if (!choices.some((choice) => choice.id === current)) {
    return [{ value: current, label: current }, ...options];
  }
  return options;
}

/**
 * Words for how many times a Thought Experiment was asked.
 *
 * @param count - How many times it was put to a User.
 * @returns "time asked" for one, "times asked" otherwise.
 */
export function askedWords(count: number): string {
  return count === 1 ? "time asked" : "times asked";
}

/**
 * Finds the sensitivity a select chose.
 *
 * @param chosen - The chosen option's value.
 * @returns That sensitivity; low when the value is none of them.
 */
export function sensitivityOf(chosen: string): ThoughtExperimentSensitivity {
  return (
    SENSITIVITY_OPTIONS.find((option) => option.value === chosen)?.value ??
    "low"
  );
}
