"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MenuIcon } from "@/components/MenuIcon";
import { foldButton, menuLinkHover } from "@/components/menu-styles";
import { useSignOut } from "@/lib/auth/client";
import { isUserItemCurrent, userMenuItems } from "@/lib/dashboard-menu";

/**
 * The inside of the folded sidebar: a 76px rail of icons for the User pages,
 * with Sign out at the foot. Admins unfold the menu to reach admin pages.
 *
 * @param props - `onUnfold` brings the full sidebar back.
 * @returns The rail's contents.
 */
export function SidebarRail({ onUnfold }: { onUnfold: () => void }) {
  const pathname = usePathname();
  const signOut = useSignOut();
  return (
    <div className="box-border flex min-h-full flex-col items-center gap-1.5 px-0 py-[18px]">
      <button
        type="button"
        aria-label="Unfold the menu"
        onClick={onUnfold}
        className={foldButton}
      >
        <svg
          aria-hidden="true"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10 6l6 6-6 6M5 6l6 6-6 6" />
        </svg>
      </button>
      <Link
        href="/"
        aria-label="Zeph"
        className={`flex size-11 items-center justify-center text-[24px] font-normal text-cream no-underline ${menuLinkHover}`}
      >
        Z
      </Link>
      <nav
        aria-label="Dashboard"
        className="flex flex-col items-center gap-0.5"
      >
        {userMenuItems.map((item) => {
          const isCurrent = isUserItemCurrent(item.href, pathname);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              title={item.label}
              aria-current={isCurrent ? "page" : undefined}
              className={`flex size-11 items-center justify-center rounded-input no-underline ${
                isCurrent ? "bg-panel text-cream" : `text-soft ${menuLinkHover}`
              }`}
            >
              <MenuIcon path={item.iconPath} />
            </Link>
          );
        })}
      </nav>
      <button
        type="button"
        aria-label="Sign out"
        title="Sign out"
        onClick={() => void signOut("/sign-in")}
        className={`mt-auto flex size-11 cursor-pointer items-center justify-center rounded-input border-0 bg-transparent text-soft ${menuLinkHover}`}
      >
        <MenuIcon path="M10 4H5v16h5M15 8l4 4-4 4M19 12H9" />
      </button>
    </div>
  );
}
