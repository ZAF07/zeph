import type { ReactNode } from "react";

/**
 * Wraps a control so a small note pops up above it while the mouse is over
 * it, e.g. to say why the control is locked. With no note, nothing pops up.
 * Give the control the same `id` as its described-by id so a screen reader
 * reads the note too.
 *
 * @param props - `id` is the note's id; `note` is what the pop-up says, or
 *   null for no pop-up; `children` is the control.
 * @returns The control, with its pop-up.
 */
export function HoverNote({
  id,
  note,
  children,
}: {
  id: string;
  note: string | null;
  children: ReactNode;
}) {
  return (
    <span className="group relative inline-flex">
      {children}
      {note ? (
        <span
          id={id}
          role="tooltip"
          className="pointer-events-none absolute right-0 bottom-full z-10 hidden w-max max-w-[240px] rounded-input border border-line bg-bg-deep px-3.5 py-2 text-[13px] text-soft group-hover:block"
        >
          {note}
        </span>
      ) : null}
    </span>
  );
}
