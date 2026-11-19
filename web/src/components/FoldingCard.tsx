import type { ReactNode } from "react";

import { CardTag } from "@/components/CardTag";

/**
 * One card of the card-list template. Its whole top row opens and folds it:
 * a chevron (right when folded, down when open), the title, the start of
 * its summary, any tags, and a count on the right. A card with unsaved
 * edits shows the orange "Unsaved changes" tag on that row. The open part
 * stays in the page while folded, so typed text is kept.
 *
 * @param props - `title` names the card; `summary` is the line under it;
 *   `leading` goes before the title, such as a sticker's picture;
 *   `tags` are the row's pills; `meta` is the row's right-hand count;
 *   `isDirty` shows the unsaved tag; `isOpen` and `onToggle` open and fold
 *   it; `children` are the fields and save bar shown while open.
 * @returns The card.
 */
export function FoldingCard({
  title,
  summary,
  leading,
  tags,
  meta,
  isDirty,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  summary: ReactNode;
  leading?: ReactNode;
  tags?: ReactNode;
  meta?: ReactNode;
  isDirty: boolean;
  isOpen: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section
      aria-label={title}
      className="rounded-card border border-line bg-panel"
    >
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={onToggle}
        className="box-border flex min-h-[68px] w-full cursor-pointer flex-wrap items-center gap-x-[14px] gap-y-2 rounded-card border-0 bg-transparent py-3 pr-5 pl-4 text-left text-soft"
      >
        <svg
          aria-hidden="true"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`flex-none transition-transform duration-150 ease-in-out ${isOpen ? "rotate-90" : "rotate-0"}`}
        >
          <path d="M9 6l6 6-6 6" />
        </svg>
        {leading}
        <span className="flex min-w-0 flex-[1_1_240px] flex-col gap-0.5">
          <span className="text-[16px] font-normal [overflow-wrap:anywhere] text-cream">
            {title}
          </span>
          <span className="overflow-hidden text-[13px] text-ellipsis whitespace-nowrap text-soft">
            {summary}
          </span>
        </span>
        {isDirty ? <CardTag tone="orange">Unsaved changes</CardTag> : null}
        {tags}
        {meta ? (
          <span className="flex-none text-[13px] text-soft">{meta}</span>
        ) : null}
      </button>
      <div
        hidden={!isOpen}
        className="box-border flex flex-col gap-4 pt-1 pr-5 pb-4 pl-5 min-[900px]:pl-12"
      >
        {children}
      </div>
    </section>
  );
}
