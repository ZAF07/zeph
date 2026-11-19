import { AdminPageHeader } from "@/components/AdminPageHeader";
import { AdminUsers } from "@/components/AdminUsers";

/**
 * The admin Users page.
 *
 * @returns The page.
 */
export default function AdminUsersPage() {
  return (
    <>
      <AdminPageHeader
        title="Users"
        lead="Activity counts only. You never see what anyone wrote."
      />
      <AdminUsers />
    </>
  );
}
