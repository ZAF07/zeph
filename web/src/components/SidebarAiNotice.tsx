import { readCopy, type Copy } from "@/lib/copy";

/**
 * The short AI notice in the sidebar and phone menu.
 *
 * @param props - `copy` is the menu's Copy.
 * @returns The notice.
 */
export function SidebarAiNotice({ copy }: { copy: Copy }) {
  return (
    <p className="m-0 px-3.5 text-[12px] text-soft">
      {readCopy(copy, "shared.dashboard.ai_notice")}
    </p>
  );
}
