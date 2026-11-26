import { codeTextArea, fieldLabel, inputField } from "@/components/form-styles";
import type { NeedOverride } from "@/lib/api-client";
import {
  curiosityTreatmentOptions,
  defaultCuriosityTreatment,
  toCuriosityTreatment,
} from "@/lib/curiosity-treatment";

/**
 * The fields of a Need override: its three texts and how Curiosities are
 * treated.
 *
 * @param props - `label` names the Need; `value` is the override, or null
 *   if it is malformed; `onChange` gets the new details.
 * @returns The fields.
 */
export function NeedOverrideFields({
  label,
  value,
  onChange,
}: {
  label: string;
  value: NeedOverride | null;
  onChange: (value: NeedOverride) => void;
}) {
  const details = value ?? { name: "", when_it_fits: "", how_to_reply: "" };
  return (
    <div className="flex flex-col gap-3">
      <label className={fieldLabel}>
        Name
        <input
          aria-label={`${label} name`}
          className={inputField}
          value={details.name}
          onChange={(event) =>
            onChange({ ...details, name: event.target.value })
          }
        />
      </label>
      <label className={fieldLabel}>
        When it fits
        <textarea
          aria-label={`${label} when it fits`}
          className={codeTextArea}
          rows={3}
          value={details.when_it_fits}
          onChange={(event) =>
            onChange({ ...details, when_it_fits: event.target.value })
          }
        />
      </label>
      <label className={fieldLabel}>
        How to reply
        <textarea
          aria-label={`${label} how to reply`}
          className={codeTextArea}
          rows={3}
          value={details.how_to_reply}
          onChange={(event) =>
            onChange({ ...details, how_to_reply: event.target.value })
          }
        />
      </label>
      <label className={fieldLabel}>
        Curiosities
        <select
          aria-label={`${label} Curiosities`}
          className={inputField}
          value={details.curiosities ?? defaultCuriosityTreatment}
          onChange={(event) =>
            onChange({
              ...details,
              curiosities: toCuriosityTreatment(event.target.value),
            })
          }
        >
          {curiosityTreatmentOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
