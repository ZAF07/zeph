"use client";

import { useId } from "react";

import { CardCheckbox } from "@/components/CardCheckbox";
import { CardTextField } from "@/components/CardTextField";
import { FieldRow } from "@/components/FieldRow";
import { FieldSelect } from "@/components/FieldSelect";
import type { FeatureSwitch, MoveInput } from "@/lib/api-client";

/**
 * A Move's fields inside its card or the add box: name, "when it fits",
 * "how to do it", then field rows for the Feature it needs and whether it
 * asks a question.
 *
 * @param props - `value` is the Move as edited; `features` are the
 *   Features it can need; `onChange` gets the edited Move.
 * @returns The fields.
 */
export function MoveFields({
  value,
  features,
  onChange,
}: {
  value: MoveInput;
  features: FeatureSwitch[];
  onChange: (value: MoveInput) => void;
}) {
  const fieldId = useId();

  function chooseFeature(chosen: string) {
    const feature = features.find((option) => option.feature === chosen);
    onChange({ ...value, needed_feature: feature ? feature.feature : null });
  }

  return (
    <>
      <CardTextField
        label="Name"
        hint="The Understanding sees this name with “when it fits” and picks Moves before each reply."
        placeholder="e.g. Research"
        value={value.name}
        onChange={(name) => onChange({ ...value, name })}
      />
      <CardTextField
        label="When it fits"
        hint="The Understanding reads this before each reply to pick the Moves that help right now."
        value={value.when_it_fits}
        multiline
        onChange={(whenItFits) =>
          onChange({ ...value, when_it_fits: whenItFits })
        }
      />
      <CardTextField
        label="How to do it"
        hint="Goes into the Reply’s instructions when the Understanding picks this Move."
        value={value.how_to_do_it}
        multiline
        onChange={(howToDoIt) =>
          onChange({ ...value, how_to_do_it: howToDoIt })
        }
      />
      <ul className="m-0 list-none p-0">
        <FieldRow
          title="Needs a Feature"
          caption="Never offered to the Understanding when that Feature doesn’t work for the User."
          htmlFor={`${fieldId}-feature`}
        >
          <FieldSelect
            id={`${fieldId}-feature`}
            value={value.needed_feature ?? ""}
            options={[
              { value: "", label: "None" },
              ...features.map((feature) => ({
                value: feature.feature,
                label: feature.name,
              })),
            ]}
            onChange={chooseFeature}
          />
        </FieldRow>
        <FieldRow
          title="Asks a question"
          caption="Never offered to the Understanding right after a reply that made it, or with another question."
          htmlFor={`${fieldId}-asks`}
        >
          <CardCheckbox
            id={`${fieldId}-asks`}
            checked={value.asks_a_question}
            onChange={(asksAQuestion) =>
              onChange({ ...value, asks_a_question: asksAQuestion })
            }
          />
        </FieldRow>
      </ul>
    </>
  );
}
