import type { ReactNode } from "react";

/**
 * The note shown when a change could not be saved. It says what failed and
 * that what the person typed is kept.
 *
 * @param props - `children` is the message.
 * @returns The note.
 */
export function SaveFailedNote({ children }: { children: ReactNode }) {
  return (
    <p
      role="alert"
      className="m-0 rounded-note border border-danger bg-transparent px-[18px] py-3 text-[14px] text-danger"
    >
      {children}
    </p>
  );
}
