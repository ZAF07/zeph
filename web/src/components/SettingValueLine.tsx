import { describeSettingValue } from "@/lib/setting-overrides";

/**
 * One labelled setting value, such as its live value when a run started.
 *
 * @param props - `name` says which value it is; `value` is the value.
 * @returns The line, keeping the text's line breaks.
 */
export function SettingValueLine({
  name,
  value,
}: {
  name: string;
  value: unknown;
}) {
  return (
    <span className="break-words whitespace-pre-wrap text-text">
      <span className="text-soft">{name}:</span> {describeSettingValue(value)}
    </span>
  );
}
