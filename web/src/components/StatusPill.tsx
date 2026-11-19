import type { ReactNode } from "react";

/**
 * A small pill in an admin table cell, such as an outcome or a role. A
 * `filled` pill is cream; otherwise it is outlined. A `danger` pill is
 * outlined in the danger colour, for errors and failures.
 *
 * @param props - `filled` picks the cream look; `danger` picks the danger
 *   look; `children` is the text.
 * @returns The pill.
 */
export function StatusPill({
  filled,
  danger = false,
  children,
}: {
  filled: boolean;
  danger?: boolean;
  children: ReactNode;
}) {
  const look = filled
    ? "bg-cream text-ink"
    : danger
      ? "border border-danger text-danger"
      : "border border-line-strong text-soft";
  return (
    <span
      className={`rounded-pill px-2.5 py-0.5 text-[12px] font-normal whitespace-nowrap ${look}`}
    >
      {children}
    </span>
  );
}
