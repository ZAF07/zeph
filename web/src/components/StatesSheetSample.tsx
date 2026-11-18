import type { ReactNode } from "react";

/**
 * One labelled sample on the `States` preview sheet.
 *
 * @param props - `label` says where the sample is used, `wide` gives it the
 *   wider column the confirm dialog needs, and `children` is the sample.
 * @returns The sample.
 */
export function StatesSheetSample({
  label,
  wide = false,
  children,
}: {
  label: string;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`flex min-w-0 flex-col gap-2.5 ${wide ? "flex-[1_1_460px]" : "flex-[1_1_360px]"}`}
    >
      <div className="text-[13px] font-normal text-text">{label}</div>
      {children}
    </div>
  );
}
