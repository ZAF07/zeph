import { AdminPageHeader } from "@/components/AdminPageHeader";
import { MemoryCategoriesManager } from "@/components/MemoryCategoriesManager";

/**
 * The admin Memory Categories page: how Zeph sorts what it remembers.
 *
 * @returns The page.
 */
export default function AdminMemoryCategoriesPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Memory Categories"
        lead="How Zeph sorts what it remembers. Names appear to Users on their Memories page."
      />
      <MemoryCategoriesManager />
    </div>
  );
}
