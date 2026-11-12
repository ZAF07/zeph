import { AdminPageHeader } from "@/components/AdminPageHeader";
import { StickerLibrary } from "@/components/StickerLibrary";

/**
 * The admin Sticker Library page: the Telegram stickers Zeph may send.
 *
 * @returns The page.
 */
export default function AdminStickersPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Sticker Library"
        lead="Telegram stickers Zeph may send. Zeph reads each “when to use” note and uses them sparingly."
      />
      <StickerLibrary />
    </div>
  );
}
