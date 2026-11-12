import type { ReactNode } from "react";

/**
 * A setting's name with a short grey line under it, at the start of a
 * settings row.
 *
 * @param props - `title` names the setting, `caption` explains it and
 *   `note` is an optional extra line under the caption.
 * @returns The label block.
 */
export function SettingLabel({
  title,
  caption,
  note,
}: {
  title: string;
  caption: string;
  note?: ReactNode;
}) {
  return (
    <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-0.5">
      <span className="font-semibold">{title}</span>
      <span className="text-caption text-ink-muted">{caption}</span>
      {note}
    </span>
  );
}
