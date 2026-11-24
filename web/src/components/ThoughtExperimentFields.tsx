"use client";

import { useId } from "react";

import { CardTextField } from "@/components/CardTextField";
import { FieldRow } from "@/components/FieldRow";
import { FieldSelect } from "@/components/FieldSelect";
import { Switch } from "@/components/Switch";
import type {
  PatternTypeChoice,
  ThoughtExperimentInput,
  ThoughtExperimentSensitivity,
} from "@/lib/api-client";
import {
  SENSITIVITY_OPTIONS,
  patternTypeOptions,
} from "@/lib/thought-experiment-draft";

/**
 * A Thought Experiment's fields inside its card or the add box: the
 * wording, then field rows for the two Pattern Types it tells apart, its
 * sensitivity, whether it is a starter and whether it is on. Each has a
 * hint.
 *
 * @param props - `value` is the Thought Experiment as edited;
 *   `patternTypes` are the catalog's Pattern Types to pick from;
 *   `onChange` gets the edited Thought Experiment.
 * @returns The fields.
 */
export function ThoughtExperimentFields({
  value,
  patternTypes,
  onChange,
}: {
  value: ThoughtExperimentInput;
  patternTypes: PatternTypeChoice[];
  onChange: (value: ThoughtExperimentInput) => void;
}) {
  const fieldId = useId();

  return (
    <>
      <CardTextField
        label="Wording"
        hint="What Zeph puts to the User, in these words. One made-up situation, ending in an open question that leaves every choice open."
        placeholder="e.g. A close friend asks you to read their speech, and it isn’t good. What do you tell them?"
        value={value.wording}
        multiline
        onChange={(wording) => onChange({ ...value, wording })}
      />
      <ul className="m-0 list-none p-0">
        <FieldRow
          title="Pattern Type"
          caption="One of the two look-alikes its answer tells apart."
          htmlFor={`${fieldId}-first`}
        >
          <FieldSelect
            id={`${fieldId}-first`}
            value={value.pattern_type_id}
            options={patternTypeOptions(patternTypes, value.pattern_type_id)}
            onChange={(chosen) =>
              onChange({ ...value, pattern_type_id: chosen })
            }
          />
        </FieldRow>
        <FieldRow
          title="Its look-alike"
          caption="The other one. Zeph asks it when a User’s unclear stories sit between these two."
          htmlFor={`${fieldId}-other`}
        >
          <FieldSelect
            id={`${fieldId}-other`}
            value={value.other_pattern_type_id}
            options={patternTypeOptions(
              patternTypes,
              value.other_pattern_type_id,
            )}
            onChange={(chosen) =>
              onChange({ ...value, other_pattern_type_id: chosen })
            }
          />
        </FieldRow>
        <FieldRow
          title="Sensitivity"
          caption="How personal it is. A more sensitive one waits for the right moment, like any Curiosity."
          htmlFor={`${fieldId}-sensitivity`}
        >
          <FieldSelect
            id={`${fieldId}-sensitivity`}
            value={value.sensitivity}
            options={SENSITIVITY_OPTIONS}
            onChange={(chosen) =>
              onChange({
                ...value,
                sensitivity: chosen as ThoughtExperimentSensitivity,
              })
            }
          />
        </FieldRow>
        <FieldRow
          title="Starter"
          caption="Broad enough to put to a new User in their first Conversations. Keep one per area."
        >
          <Switch
            label="Starter"
            checked={value.starter}
            onChange={(starter) => onChange({ ...value, starter })}
          />
        </FieldRow>
        <FieldRow
          title="On"
          caption="Zeph asks it only while it is on. Switching it off closes any Curiosity waiting to ask it."
        >
          <Switch
            label="On"
            checked={value.on}
            onChange={(on) => onChange({ ...value, on })}
          />
        </FieldRow>
      </ul>
    </>
  );
}
