import Link from "next/link";

import { SidebarAccount } from "@/components/SidebarAccount";
import { SidebarAiNotice } from "@/components/SidebarAiNotice";
import { SidebarNav } from "@/components/SidebarNav";
import { ZephLogo } from "@/components/ZephLogo";
import type { SidebarItem } from "@/components/SidebarNav";

/** The User pages, in the order the sidebar shows them. */
const userSidebarItems: SidebarItem[] = [
  {
    id: "home",
    label: "Home",
    href: "/",
    iconPath: "M4 10.5L12 4l8 6.5V20H4zM10 20v-5h4v5",
  },
  {
    id: "memories",
    label: "Memories",
    href: "/memories",
    iconPath: "M12 3v4M12 17v4M3 12h4M17 12h4M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8",
  },
  {
    id: "check-ins",
    label: "Check-ins",
    href: "/check-ins",
    iconPath: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 7v5l3 2",
  },
  {
    id: "account",
    label: "Account & privacy",
    href: "/account",
    iconPath: "M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6z",
  },
];

/**
 * The Dashboard sidebar: logo, navigation, the AI notice and who is signed in.
 *
 * @returns The sidebar.
 */
export function Sidebar() {
  return (
    <aside className="flex h-full min-h-full w-full flex-col gap-6 border-r border-line bg-subtle px-4 py-6 leading-[1.4]">
      <span
        aria-hidden="true"
        className="brand-stripe -mx-4 -mt-6 mb-2 block h-0.5"
      />
      <Link
        href="/"
        aria-label="Zeph home"
        className="flex items-center gap-2.5 px-3 text-ink no-underline"
      >
        <ZephLogo />
        <span className="text-2xl">Zeph</span>
      </Link>

      <SidebarNav items={userSidebarItems} />

      <div className="mt-auto flex flex-col gap-2.5 px-1">
        <SidebarAiNotice />
        <SidebarAccount />
      </div>
    </aside>
  );
}
