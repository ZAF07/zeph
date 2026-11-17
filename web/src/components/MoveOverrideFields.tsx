import { codeTextArea, fieldLabel, inputField } from "@/components/form-styles";
import type { MoveOverride } from "@/lib/api-client";

/**
 * The three fields of a Move override: its text, never its needed Feature.
 *
 * @param props - `label` names the Move; `value` is the override, or null
 *   if it is malformed; `onChange` gets the new text.
 * @returns The fields.
 */
export function MoveOverrideFields({
  label,
  value,
  onChange,
}: {
  label: string;
  value: MoveOverride | null;
  onChange: (value: MoveOverride) => void;
}) {
  const text = value ?? { name: "", when_it_fits: "", how_to_do_it: "" };
  return (
    <div className="flex flex-col gap-3">
      <label className={fieldLabel}>
        Name
        <input
          aria-label={`${label} name`}
          className={inputField}
          value={text.name}
          onChange={(event) => onChange({ ...text, name: event.target.value })}
        />
      </label>
      <label className={fieldLabel}>
        When it fits
        <textarea
          aria-label={`${label} when it fits`}
          className={codeTextArea}
          rows={3}
          value={text.when_it_fits}
          onChange={(event) =>
            onChange({ ...text, when_it_fits: event.target.value })
          }
        />
      </label>
      <label className={fieldLabel}>
        How to do it
        <textarea
          aria-label={`${label} how to do it`}
          className={codeTextArea}
          rows={3}
          value={text.how_to_do_it}
          onChange={(event) =>
            onChange({ ...text, how_to_do_it: event.target.value })
          }
        />
      </label>
    </div>
  );
}
