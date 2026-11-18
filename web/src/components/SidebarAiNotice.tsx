"use client";

import { usePlatformContent } from "@/lib/queries";

/**
 * The short AI notice in the sidebar and phone menu, worded by Admins.
 *
 * @returns The notice, or nothing until the wording has loaded.
 */
export function SidebarAiNotice() {
  const notice = usePlatformContent().data?.ai_notice_short;

  if (!notice) {
    return null;
  }

  return <p className="m-0 px-3.5 text-[12px] text-soft">{notice}</p>;
}
