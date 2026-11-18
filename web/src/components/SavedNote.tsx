import type { ReactNode } from "react";

/**
 * The note shown after a change was saved.
 *
 * @param props - `children` is the message, starting "Saved.".
 * @returns The note.
 */
export function SavedNote({ children }: { children: ReactNode }) {
  return (
    <p
      role="status"
      className="m-0 rounded-note border border-line bg-panel px-[18px] py-3 text-[14px] text-text"
    >
      {children}
    </p>
  );
}
