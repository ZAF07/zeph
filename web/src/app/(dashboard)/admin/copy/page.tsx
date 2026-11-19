import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CopyEditor } from "@/components/CopyEditor";

/**
 * The admin Copy page, where Admins change the words on the website.
 *
 * @returns The page.
 */
export default function AdminCopyPage() {
  return (
    <>
      <AdminPageHeader
        title="Copy"
        lead="The words Users and visitors read on the website, one tab per page. The design decides how they look."
      />
      <CopyEditor />
    </>
  );
}
