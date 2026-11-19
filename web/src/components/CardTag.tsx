import type { ReactNode } from "react";

/**
 * The pill's colours: plain for facts about the item, orange for unsaved or
 * needing attention, danger for something that failed.
 */
const toneClass = {
  plain: "border-line-strong text-soft",
  orange: "border-orange font-normal text-orange",
  danger: "border-danger text-danger",
};

/**
 * A small pill on a card's folded row, such as "Unsaved changes" or
 * "Sends a Shared Photo". A padlock marks a fact that can't be changed here.
 *
 * @param props - `tone` picks the colours; `locked` adds the padlock;
 *   `children` is the text.
 * @returns The pill.
 */
export function CardTag({
  tone = "plain",
  locked = false,
  children,
}: {
  tone?: "plain" | "orange" | "danger";
  locked?: boolean;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-pill border px-2.5 py-0.5 text-[12px] ${toneClass[tone]}`}
    >
      {locked ? (
        <svg
          aria-hidden="true"
          width="10"
          height="12"
          viewBox="0 0 12 14"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        >
          <rect x="1.5" y="6" width="9" height="7" rx="1.5" />
          <path d="M3.5 6V4a2.5 2.5 0 0 1 5 0v2" />
        </svg>
      ) : null}
      {children}
    </span>
  );
}
