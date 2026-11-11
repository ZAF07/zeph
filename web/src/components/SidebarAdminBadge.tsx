"use client";

import { useIsAdmin } from "@/lib/use-is-admin";

/**
 * The small "Admin" badge beside an Admin's name in the sidebar.
 *
 * @returns The badge, or nothing for Users who are not Admins.
 */
export function SidebarAdminBadge() {
  const isAdmin = useIsAdmin();
  if (!isAdmin) {
    return null;
  }
  return (
    <span className="rounded-full bg-ink px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-white">
      Admin
    </span>
  );
}
