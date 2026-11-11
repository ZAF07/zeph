import type { ReactNode } from "react";

import { AdminGate } from "@/components/AdminGate";

/**
 * The column the admin pages sit in: wider than the User pages, for tables
 * and editors. Only Admins see the pages.
 *
 * @param props - `children` is the admin page.
 * @returns The page in its column.
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto flex max-w-[1120px] flex-col gap-8 text-sm">
      <AdminGate>{children}</AdminGate>
    </div>
  );
}
