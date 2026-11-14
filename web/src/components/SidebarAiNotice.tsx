"use client";

import { usePlatformContent } from "@/lib/queries";

/**
 * The short AI notice at the foot of the sidebar, worded by Admins.
 *
 * @returns The notice, or nothing until the wording has loaded.
 */
export function SidebarAiNotice() {
  const notice = usePlatformContent().data?.ai_notice_short;

  if (!notice) {
    return null;
  }

  return (
    <p className="m-0 flex items-start gap-1.5 px-2 text-xs text-ink-muted">
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        aria-hidden="true"
        className="mt-px flex-none"
      >
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8v4M12 16h.01" />
      </svg>
      <span>{notice}</span>
    </p>
  );
}
