/**
 * Writes a stored value for reading: text as it is, anything else as JSON.
 *
 * @param value - The value.
 * @returns The text to show.
 */
function showValue(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

/**
 * One group of named values in a run's snapshot, such as its Platform
 * Settings, each value under its name.
 *
 * @param props - `title` names the group; `values` holds its values by name.
 * @returns The group, folded away until opened.
 */
export function SnapshotValueGroup({
  title,
  values,
}: {
  title: string;
  values: Record<string, unknown>;
}) {
  return (
    <details className="rounded-tile border border-line px-3.5 py-2.5">
      <summary className="cursor-pointer text-[13px] text-text">
        {title}
      </summary>
      <dl className="m-0 mt-2 flex flex-col gap-2">
        {Object.entries(values).map(([name, value]) => (
          <div key={name} className="flex flex-col gap-0.5">
            <dt className="font-mono text-[12px] text-soft">{name}</dt>
            <dd className="m-0">
              <pre className="m-0 max-h-60 overflow-auto rounded-input bg-bg-deep px-2.5 py-1.5 font-mono text-[12px] whitespace-pre-wrap">
                {showValue(value)}
              </pre>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
