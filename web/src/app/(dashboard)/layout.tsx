import type { ReactNode } from "react";

import { DashboardFrame } from "@/components/DashboardFrame";

/**
 * The layout of every signed-in page except Home, which the `/` page puts
 * in the same frame itself.
 *
 * @param props - `children` is the page.
 * @returns The page in the Dashboard frame.
 */
export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <DashboardFrame>{children}</DashboardFrame>;
}
