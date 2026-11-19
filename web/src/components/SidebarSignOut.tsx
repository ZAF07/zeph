"use client";

import { menuLinkHover } from "@/components/menu-styles";
import { useSignOut } from "@/lib/auth/client";
import { readCopy, type Copy } from "@/lib/copy";

/**
 * The underlined "Sign out" link in the sidebar and phone menu.
 *
 * @param props - `copy` is the menu's Copy; `className` places it: padding in the sidebar, none in the menu.
 * @returns The button that signs the User out.
 */
export function SidebarSignOut({
  copy,
  className = "",
}: {
  copy: Copy;
  className?: string;
}) {
  const signOut = useSignOut();
  return (
    <button
      type="button"
      onClick={() => void signOut("/sign-in")}
      className={`flex min-h-11 cursor-pointer items-center border-0 bg-transparent text-[13px] text-soft underline ${menuLinkHover} ${className}`}
    >
      {readCopy(copy, "shared.dashboard.sign_out")}
    </button>
  );
}
