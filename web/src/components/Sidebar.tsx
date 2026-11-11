import Link from "next/link";

import { SidebarNav } from "@/components/SidebarNav";
import { ZephLogo } from "@/components/ZephLogo";
import type { SidebarItem } from "@/components/SidebarNav";
import type { CurrentAccount } from "@/lib/auth/server";

/** The User pages built so far; later issues add Memories, Check-ins and more. */
const userSidebarItems: SidebarItem[] = [
  {
    id: "home",
    label: "Home",
    href: "/",
    iconPath: "M4 10.5L12 4l8 6.5V20H4zM10 20v-5h4v5",
  },
];

/**
 * The Dashboard sidebar: logo, navigation, the AI notice and who is signed in.
 *
 * @param props - `account` is the signed-in person.
 * @returns The sidebar.
 */
export function Sidebar({ account }: { account: CurrentAccount }) {
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
          <span>Zeph is an AI, not a therapist or crisis service.</span>
        </p>
        <div className="flex items-center gap-2.5 p-2">
          <span
            aria-hidden="true"
            className="flex size-8 flex-none items-center justify-center rounded-full bg-blue text-caption font-semibold text-white"
          >
            {account.name.charAt(0).toUpperCase()}
          </span>
          <span className="flex min-w-0 flex-col text-caption leading-[1.3]">
            <span className="font-semibold">{account.name}</span>
            <span className="overflow-hidden text-ellipsis text-ink-muted">
              {account.email}
            </span>
          </span>
        </div>
      </div>
    </aside>
  );
}
