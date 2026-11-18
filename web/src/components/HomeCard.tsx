import type { ReactNode } from "react";

/** How wide a card starts before the row wraps, as drawn. */
const basisClasses = {
  narrow: "flex-[1_1_320px]",
  wide: "flex-[1_1_380px]",
};

/**
 * A titled panel on the Dashboard home, such as Telegram or Plan.
 *
 * @param props - `headingId` ties the title to the section, `title` names
 *   the card, `aside` sits at the right of the title (a pill or a link),
 *   `caption` is an optional line under the title, `basis` is how wide the
 *   card starts before its row wraps, and `children` is the card's body.
 * @returns The card.
 */
export function HomeCard({
  headingId,
  title,
  aside,
  caption,
  basis,
  children,
}: {
  headingId: string;
  title: ReactNode;
  aside?: ReactNode;
  caption?: string;
  basis: keyof typeof basisClasses;
  children: ReactNode;
}) {
  return (
    <section
      aria-labelledby={headingId}
      className={`box-border min-w-0 rounded-card border border-line bg-panel px-6 py-[22px] ${basisClasses[basis]}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2
          id={headingId}
          className="m-0 flex items-center text-[17px] font-normal text-cream"
        >
          {title}
        </h2>
        {aside}
      </div>
      {caption ? (
        <p className="mt-1 mb-0 text-[13px] text-soft">{caption}</p>
      ) : null}
      <div className="mt-4">{children}</div>
    </section>
  );
}
