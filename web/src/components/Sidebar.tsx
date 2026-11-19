import Link from "next/link";

import { foldButton, menuLinkHover } from "@/components/menu-styles";
import { SidebarAccount } from "@/components/SidebarAccount";
import { SidebarAiNotice } from "@/components/SidebarAiNotice";
import { SidebarNav } from "@/components/SidebarNav";
import { SidebarSignOut } from "@/components/SidebarSignOut";
import { readCopy, type Copy } from "@/lib/copy";

/**
 * The inside of the Dashboard sidebar at 900px and wider: the wordmark and
 * fold button, the menu, then the AI notice, who is signed in and Sign out.
 *
 * @param props - `copy` is the menu's Copy; `onFold` swaps the sidebar for the icon rail.
 * @returns The sidebar's contents.
 */
export function Sidebar({ copy, onFold }: { copy: Copy; onFold: () => void }) {
  return (
    <div className="box-border flex min-h-full flex-col gap-1.5 px-4 py-[18px]">
      <div className="flex items-center justify-between gap-2 pt-0 pr-0 pb-3 pl-3.5">
        <Link
          href="/"
          className={`text-[26px] font-normal text-cream no-underline ${menuLinkHover}`}
        >
          {readCopy(copy, "shared.wordmark")}
        </Link>
        <button
          type="button"
          aria-label={readCopy(copy, "shared.dashboard.fold_menu")}
          onClick={onFold}
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
            <path d="M14 6l-6 6 6 6M19 6l-6 6 6 6" />
          </svg>
        </button>
      </div>
      <SidebarNav copy={copy} />
      <div className="mt-auto flex flex-col gap-3 pt-5">
        <SidebarAiNotice />
        <SidebarAccount copy={copy} />
        <SidebarSignOut copy={copy} className="px-3.5" />
      </div>
    </div>
  );
}
