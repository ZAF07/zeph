import {
  codeTextArea,
  fieldCaption,
  inputField,
} from "@/components/form-styles";
import { NeedOverrideFields } from "@/components/NeedOverrideFields";
import { Switch } from "@/components/Switch";
import type { OverridableSetting } from "@/lib/api-client";
import { describeSettingValue, isNeedOverride } from "@/lib/setting-overrides";

/**
 * The field for one Setting Override, of the same kind the settings pages
 * use: a text box, a whole number, a model to pick, an on/off switch, or a
 * Need's name, when it fits and how to reply. It shows the live value next
 * to it.
 *
 * @param props - `label` names the setting; `setting` is its rule, or null
 *   for a Need; `models` are the models a model setting can pick; `liveValue`
 *   is its live value; `value` is the override; `onChange` gets a new value
 *   and `onRemove` drops the override.
 * @returns The field.
 */
export function SettingOverrideField({
  label,
  setting,
  models,
  liveValue,
  value,
  onChange,
  onRemove,
}: {
  label: string;
  setting: OverridableSetting | null;
  models: string[];
  liveValue: unknown;
  value: unknown;
  onChange: (value: unknown) => void;
  onRemove: () => void;
}) {
  const liveNote =
    setting?.kind === "text" || setting === null
      ? null
      : `Live: ${describeSettingValue(liveValue)}`;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-line bg-white px-3.5 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">{label}</span>
        <button
          type="button"
          className="cursor-pointer border-0 bg-transparent p-0 text-caption text-danger"
          onClick={onRemove}
          aria-label={`Stop changing ${label}`}
        >
          Remove
        </button>
      </div>
      {setting?.hint ? <p className={fieldCaption}>{setting.hint}</p> : null}
      {setting === null ? (
        <NeedOverrideFields
          label={label}
          value={isNeedOverride(value) ? value : null}
          onChange={onChange}
        />
      ) : setting.kind === "on_off" ? (
        <Switch
          label={label}
          checked={value === true}
          onChange={(isOn) => onChange(isOn)}
        />
      ) : setting.kind === "model" ? (
        <select
          aria-label={label}
          className={inputField}
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        >
          {models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      ) : setting.kind === "whole_number" ? (
        <input
          aria-label={label}
          type="number"
          className={inputField}
          min={setting.minimum}
          max={setting.maximum}
          step={1}
          value={typeof value === "number" ? value : ""}
          onChange={(event) =>
            onChange(
              event.target.value === "" ? null : Number(event.target.value),
            )
          }
        />
      ) : (
        <textarea
          aria-label={label}
          className={codeTextArea}
          rows={6}
          maxLength={setting.max_length}
          value={typeof value === "string" ? value : ""}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
      {liveNote ? <p className={fieldCaption}>{liveNote}</p> : null}
    </div>
  );
}
