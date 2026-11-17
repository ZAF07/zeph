import { compactSecondaryButton } from "@/components/button-styles";
import { inputField } from "@/components/form-styles";
import { SettingOverrideField } from "@/components/SettingOverrideField";
import type { OverrideChoices, SettingOverrides } from "@/lib/api-client";
import {
  describeVariantSettings,
  overrideLabel,
} from "@/lib/setting-overrides";

/**
 * One Variant of a new run: the live settings, plus any Setting Overrides
 * the Admin adds. Picking a setting, Need or Move to change starts it from
 * its live value; the live settings are never touched.
 *
 * @param props - `letter` is the Variant's letter; `overrides` its Setting
 *   Overrides; `choices` what can be overridden; `onChange` gets the new
 *   overrides; `onRemove`, when given, drops the whole Variant.
 * @returns The Variant's card.
 */
export function VariantOverridesEditor({
  letter,
  overrides,
  choices,
  onChange,
  onRemove,
}: {
  letter: string;
  overrides: SettingOverrides;
  choices: OverrideChoices;
  onChange: (overrides: SettingOverrides) => void;
  onRemove?: () => void;
}) {
  const keys = Object.keys(overrides);
  const settingsLeft = choices.settings.filter(
    (setting) => !(setting.key in overrides),
  );
  const needsLeft = choices.needs.filter((need) => !(need.key in overrides));
  const movesLeft = choices.moves.filter((move) => !(move.key in overrides));

  function liveValueOf(key: string): unknown {
    return (
      choices.settings.find((setting) => setting.key === key)?.value ??
      choices.needs.find((need) => need.key === key)?.value ??
      choices.moves.find((move) => move.key === key)?.value
    );
  }

  function add(key: string) {
    onChange({ ...overrides, [key]: liveValueOf(key) });
  }

  function remove(key: string) {
    const rest = { ...overrides };
    delete rest[key];
    onChange(rest);
  }

  return (
    <section
      aria-label={`Variant ${letter}`}
      className="flex flex-col gap-3 rounded-xl border border-line bg-subtle px-[18px] py-3.5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="m-0 text-body font-semibold">
          Variant {letter}{" "}
          <span className="font-normal text-ink-muted">
            · {describeVariantSettings(keys.length)}
          </span>
        </h3>
        {onRemove ? (
          <button
            type="button"
            className={compactSecondaryButton}
            onClick={onRemove}
          >
            Remove Variant {letter}
          </button>
        ) : null}
      </div>
      {keys.map((key) => (
        <SettingOverrideField
          key={key}
          overrideKey={key}
          label={overrideLabel(key, choices)}
          setting={
            choices.settings.find((setting) => setting.key === key) ?? null
          }
          models={choices.models}
          liveValue={liveValueOf(key)}
          value={overrides[key]}
          onChange={(value) => onChange({ ...overrides, [key]: value })}
          onRemove={() => remove(key)}
        />
      ))}
      <select
        aria-label={`Change a setting in Variant ${letter}`}
        className={inputField}
        value=""
        onChange={(event) => {
          if (event.target.value) {
            add(event.target.value);
          }
        }}
      >
        <option value="">Change a setting for this Variant only…</option>
        <optgroup label="Platform Settings">
          {settingsLeft.map((setting) => (
            <option key={setting.key} value={setting.key}>
              {setting.label}
            </option>
          ))}
        </optgroup>
        <optgroup label="Needs">
          {needsLeft.map((need) => (
            <option key={need.key} value={need.key}>
              Need: {need.name}
            </option>
          ))}
        </optgroup>
        <optgroup label="Moves">
          {movesLeft.map((move) => (
            <option key={move.key} value={move.key}>
              Move: {move.name}
            </option>
          ))}
        </optgroup>
      </select>
    </section>
  );
}
