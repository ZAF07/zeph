"use client";

import { useSearchParams } from "next/navigation";
import { useState, type ReactNode } from "react";

import { PhoneBar } from "@/components/PhoneBar";
import { PhoneMenu } from "@/components/PhoneMenu";
import { Sidebar } from "@/components/Sidebar";
import { SidebarRail } from "@/components/SidebarRail";
import { hasDesignFlag } from "@/lib/design-flags";
import { useMenuFolded } from "@/lib/use-menu-folded";

/** The phone menu panel's id, which the menu button points to. */
const PHONE_MENU_ID = "phone-menu";

/**
 * The frame every signed-in page sits in. At 900px and wider, a sticky
 * sidebar that folds into an icon rail; below that, a sticky top bar whose
 * button opens the menu above the page. `?design=menu-open` opens the phone
 * menu in design-fixture mode.
 *
 * @param props - `children` is the page.
 * @returns The page in its frame.
 */
export function DashboardShell({ children }: { children: ReactNode }) {
  const forcedMenuOpen = hasDesignFlag(useSearchParams(), "menu-open");
  const [phoneMenuOpen, setPhoneMenuOpen] = useState(forcedMenuOpen);
  const [menuFolded, setMenuFolded] = useMenuFolded();
  const sidebarWidth = menuFolded ? "flex-[0_0_76px]" : "flex-[1_1_240px]";

  return (
    <div className="flex min-h-screen flex-col min-[900px]:flex-row min-[900px]:flex-wrap">
      <PhoneBar
        menuId={PHONE_MENU_ID}
        menuOpen={phoneMenuOpen}
        onMenuToggle={() => setPhoneMenuOpen(!phoneMenuOpen)}
      />
      {phoneMenuOpen ? (
        <PhoneMenu
          id={PHONE_MENU_ID}
          onLinkChoose={() => setPhoneMenuOpen(false)}
        />
      ) : null}
      <aside
        className={`sticky top-0 box-border hidden h-screen max-w-full self-start overflow-y-auto border-r border-line bg-bg-deep min-[900px]:block [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-[3px] [&::-webkit-scrollbar-thumb]:bg-line ${sidebarWidth}`}
      >
        {menuFolded ? (
          <SidebarRail onUnfold={() => setMenuFolded(false)} />
        ) : (
          <Sidebar onFold={() => setMenuFolded(true)} />
        )}
      </aside>
      <main className="box-border flex min-w-0 flex-1 flex-col gap-5 px-4 pt-5 pb-12 min-[900px]:flex-[999_1_640px] min-[900px]:gap-6 min-[900px]:px-8 min-[900px]:pt-7 min-[900px]:pb-14">
        {children}
      </main>
    </div>
  );
}
