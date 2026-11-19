import { AdminPageHeader } from "@/components/AdminPageHeader";
import { MemoryCategoriesManager } from "@/components/MemoryCategoriesManager";

/**
 * The admin Memory Categories page: how Zeph sorts what it remembers.
 *
 * @returns The page.
 */
export default function AdminMemoryCategoriesPage() {
  return (
    <>
      <AdminPageHeader
        title="Memory Categories"
        lead="How Zeph sorts what it remembers. Names appear to Users on their Memories page. Categories can’t be deleted, because Memory Items belong to them: archive one instead."
      />
      <MemoryCategoriesManager />
    </>
  );
}
