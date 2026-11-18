"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MenuIcon } from "@/components/MenuIcon";
import { menuLinkHover } from "@/components/menu-styles";
import { ToBuildTag } from "@/components/ToBuildTag";
import {
  adminMenuItems,
  isAdminItemCurrent,
  userMenuItems,
} from "@/lib/dashboard-menu";
import { useIsAdmin } from "@/lib/use-is-admin";

/**
 * Class names for a menu link, marked when it is the page being viewed.
 *
 * @param size - The User links' size, or the smaller admin links'.
 * @param isCurrent - Whether the link is the page being viewed.
 * @returns The link's class names.
 */
function menuLinkClass(size: "user" | "admin", isCurrent: boolean): string {
  const sizing =
    size === "user" ? "min-h-11 text-[14px]" : "min-h-10 text-[13px]";
  const colours = isCurrent
    ? "bg-panel text-cream"
    : `text-soft ${menuLinkHover}`;
  return `flex items-center gap-3 rounded-input px-3.5 font-normal no-underline ${sizing} ${colours}`;
}

/**
 * The menu's page links, in the sidebar and the phone menu, marking the page
 * being viewed. Admins also see the Admin section.
 *
 * @param props - `onLinkChoose` runs when a link is chosen, so the phone menu can close.
 * @returns The navigation.
 */
export function SidebarNav({ onLinkChoose }: { onLinkChoose?: () => void }) {
  const pathname = usePathname();
  const isAdmin = useIsAdmin();
  return (
    <nav aria-label="Dashboard" className="flex flex-col gap-0.5">
      {userMenuItems.map((item) => {
        const isCurrent = item.href === pathname;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isCurrent ? "page" : undefined}
            onClick={onLinkChoose}
            className={menuLinkClass("user", isCurrent)}
          >
            <MenuIcon path={item.iconPath} />
            <span>
              {item.label}
              {item.toBuild ? <ToBuildTag /> : null}
            </span>
          </Link>
        );
      })}
      {isAdmin ? (
        <div
          role="group"
          aria-label="Admin"
          className="mt-3 flex flex-col gap-px border-t border-line pt-3.5"
        >
          <div className="px-3.5 pb-1.5 text-[11px] font-medium tracking-[2px] text-soft uppercase">
            Admin
          </div>
          {adminMenuItems.map((item) => {
            const isCurrent = isAdminItemCurrent(item.href, pathname);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isCurrent ? "page" : undefined}
                onClick={onLinkChoose}
                className={menuLinkClass("admin", isCurrent)}
              >
                <span>
                  {item.label}
                  {item.toBuild ? <ToBuildTag /> : null}
                </span>
              </Link>
            );
          })}
        </div>
      ) : null}
    </nav>
  );
}
