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
    <span className="whitespace-pre-wrap break-words text-ink-body">
      <span className="text-ink-muted">{name}:</span>{" "}
      {describeSettingValue(value)}
    </span>
  );
}
