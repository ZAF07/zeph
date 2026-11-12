/**
 * A setting's name with a short grey line under it, at the start of a
 * settings row.
 *
 * @param props - `title` names the setting and `caption` explains it.
 * @returns The label block.
 */
export function SettingLabel({
  title,
  caption,
}: {
  title: string;
  caption: string;
}) {
  return (
    <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-0.5">
      <span className="font-semibold">{title}</span>
      <span className="text-caption text-ink-muted">{caption}</span>
    </span>
  );
}
