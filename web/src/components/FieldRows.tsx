import type { ReactNode } from "react";

/**
 * The form template's box of field rows, for pages with several settings.
 *
 * @param props - `footnote` is the small line under the rows, such as when
 *   they were last saved; `children` are the `FieldRow`s.
 * @returns The box.
 */
export function FieldRows({
  footnote,
  children,
}: {
  footnote?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="box-border rounded-card border border-line bg-panel px-6 py-1">
      <ul className="m-0 list-none p-0">{children}</ul>
      {footnote ? (
        <p className="m-0 pb-3.5 text-[12px] text-soft">{footnote}</p>
      ) : null}
    </div>
  );
}
