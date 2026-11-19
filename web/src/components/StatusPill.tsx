import type { ReactNode } from "react";

/**
 * A small pill in an admin table cell, such as an outcome or a role. A
 * `filled` pill is cream; otherwise it is outlined.
 *
 * @param props - `filled` picks the cream look; `children` is the text.
 * @returns The pill.
 */
export function StatusPill({
  filled,
  children,
}: {
  filled: boolean;
  children: ReactNode;
}) {
  return (
    <span
      className={`rounded-pill px-2.5 py-0.5 text-[12px] font-normal ${
        filled ? "bg-cream text-ink" : "border border-line-strong text-soft"
      }`}
    >
      {children}
    </span>
  );
}
