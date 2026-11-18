import type { ReactNode } from "react";

import { dangerButton } from "@/components/button-styles";

/**
 * A row at the foot of the Account & privacy page for a deletion that can't
 * be undone: a heading and what it removes beside a coral outline button,
 * above a top line.
 *
 * @param props - `headingId` labels the section; `title` is the heading,
 *   coral when `isDanger`; `description` says what goes; `buttonLabel` names
 *   the button, which shows "Deleting…" and is locked while `isDeleting`;
 *   `onStart` is called when it is pressed; `children` is shown under the
 *   row (the confirm dialog and any result).
 * @returns The section.
 */
export function DeletionRow({
  headingId,
  title,
  isDanger = false,
  description,
  buttonLabel,
  isDeleting,
  onStart,
  children,
}: {
  headingId: string;
  title: string;
  isDanger?: boolean;
  description: ReactNode;
  buttonLabel: string;
  isDeleting: boolean;
  onStart: () => void;
  children: ReactNode;
}) {
  return (
    <section
      aria-labelledby={headingId}
      className="flex flex-col gap-3 border-t border-line pt-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex-[1_1_360px]">
          <h2
            id={headingId}
            className={`m-0 text-[17px] font-normal ${isDanger ? "text-danger" : "text-cream"}`}
          >
            {title}
          </h2>
          {description}
        </div>
        <button
          type="button"
          className={dangerButton}
          disabled={isDeleting}
          onClick={onStart}
        >
          {isDeleting ? "Deleting…" : buttonLabel}
        </button>
      </div>
      {children}
    </section>
  );
}
