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
        lead="Everyone with an account. Counts only — Admins never see what Users write."
      />
      <AdminUsers />
    </>
  );
}
