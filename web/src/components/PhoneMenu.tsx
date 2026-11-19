import { SidebarAccount } from "@/components/SidebarAccount";
import { SidebarAiNotice } from "@/components/SidebarAiNotice";
import { SidebarNav } from "@/components/SidebarNav";
import { SidebarSignOut } from "@/components/SidebarSignOut";
import type { Copy } from "@/lib/copy";

/**
 * The phone menu panel below the top bar, pushing the page down: the menu,
 * who is signed in with Sign out, and the AI notice.
 *
 * @param props - `copy` is the menu's Copy; `id` ties it to the menu button; `onLinkChoose` closes it when a link is chosen.
 * @returns The open menu.
 */
export function PhoneMenu({
  copy,
  id,
  onLinkChoose,
}: {
  copy: Copy;
  id: string;
  onLinkChoose: () => void;
}) {
  return (
    <div
      id={id}
      className="box-border flex flex-col gap-1.5 border-b border-line bg-bg-deep px-3 pt-3 pb-4 min-[900px]:hidden"
    >
      <SidebarNav copy={copy} onLinkChoose={onLinkChoose} />
      <div className="mt-2.5">
        <SidebarAccount copy={copy} action={<SidebarSignOut copy={copy} />} />
      </div>
      <SidebarAiNotice />
    </div>
  );
}
