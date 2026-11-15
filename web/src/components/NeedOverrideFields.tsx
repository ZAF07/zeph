import { fieldLabel, inputField } from "@/components/form-styles";
import type { NeedOverride } from "@/lib/api-client";

const textArea = `${inputField} resize-y font-mono text-[13.5px] leading-relaxed`;

/**
 * The three fields of a Need override.
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
          className={textArea}
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
          className={textArea}
          rows={3}
          value={details.how_to_reply}
          onChange={(event) =>
            onChange({ ...details, how_to_reply: event.target.value })
          }
        />
      </label>
    </div>
  );
}
