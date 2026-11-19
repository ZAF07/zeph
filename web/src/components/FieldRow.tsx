import type { ReactNode } from "react";

/**
 * One field row: the setting's name and what it does on the left, its
 * control on the right, wrapping under on a narrow screen. It is one item
 * of a `FieldRows` list.
 *
 * @param props - `title` names the setting; `caption` says what it does,
 *   if it needs saying;
 *   `note` is an extra line under the caption; `htmlFor` ties the name to
 *   the control's id; `children` is the control.
 * @returns The row.
 */
export function FieldRow({
  title,
  caption,
  note,
  htmlFor,
  children,
}: {
  title: string;
  caption?: string;
  note?: ReactNode;
  htmlFor?: string;
  children: ReactNode;
}) {
  const titleClass = "block text-[15px] font-normal text-text";
  return (
    <li className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2.5 border-t border-line py-4 first:border-t-0">
      <div className="min-w-0 flex-[1_1_260px]">
        {htmlFor ? (
          <label htmlFor={htmlFor} className={titleClass}>
            {title}
          </label>
        ) : (
          <div className={titleClass}>{title}</div>
        )}
        {caption ? (
          <div className="text-[13px] text-soft">{caption}</div>
        ) : null}
        {note}
      </div>
      <div className="flex min-w-0 flex-[0_1_280px] justify-end">
        {children}
      </div>
    </li>
  );
}
