"use client";

import { menuLinkHover } from "@/components/menu-styles";
import { useSignOut } from "@/lib/auth/client";

/**
 * The underlined "Sign out" link in the sidebar and phone menu.
 *
 * @param props - `className` places it: padding in the sidebar, none in the menu.
 * @returns The button that signs the User out.
 */
export function SidebarSignOut({ className = "" }: { className?: string }) {
  const signOut = useSignOut();
  return (
    <button
      type="button"
      onClick={() => void signOut("/sign-in")}
      className={`flex min-h-11 cursor-pointer items-center border-0 bg-transparent text-[13px] text-soft underline ${menuLinkHover} ${className}`}
    >
      Sign out
    </button>
  );
}
