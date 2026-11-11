import type { ReactNode } from "react";

/**
 * The column the User pages sit in.
 *
 * @param props - `children` is the page.
 * @returns The page in its column.
 */
export default function UserPagesLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex max-w-[880px] flex-col gap-8">{children}</div>
  );
}
