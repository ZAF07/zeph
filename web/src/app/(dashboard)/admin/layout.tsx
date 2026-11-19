import type { ReactNode } from "react";

import { AdminGate } from "@/components/AdminGate";

/**
 * The admin pages, which sit straight in the Dashboard's main column as the
 * admin references draw them. Only Admins see the pages.
 *
 * @param props - `children` is the admin page.
 * @returns The page, for Admins only.
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminGate>{children}</AdminGate>;
}
