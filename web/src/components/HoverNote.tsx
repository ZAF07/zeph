import type { ReactNode } from "react";

/**
 * Wraps a control so a small note pops up to its left while the mouse is over
 * it, e.g. to say why the control is locked. With no note, nothing pops up.
 * Pass `noteId` to the control as its described-by id so a screen reader
 * reads the note too.
 *
 * @param props - `noteId` is the note's id; `note` is what the pop-up says, or
 *   null for no pop-up; `children` is the control.
 * @returns The control, with its pop-up.
 */
export function HoverNote({
  noteId,
  note,
  children,
}: {
  noteId: string;
  note: string | null;
  children: ReactNode;
}) {
  return (
    <span className="group relative inline-flex">
      {children}
      {note ? (
        <span
          id={noteId}
          role="tooltip"
          className="pointer-events-none absolute top-1/2 right-full z-10 mr-2 hidden w-max max-w-[200px] -translate-y-1/2 rounded-input border border-line bg-bg-deep px-3.5 py-2 text-[13px] text-soft group-hover:block"
        >
          {note}
        </span>
      ) : null}
    </span>
  );
}
