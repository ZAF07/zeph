import { AdminPageHeader } from "@/components/AdminPageHeader";
import { AdminUsage } from "@/components/AdminUsage";

/**
 * The admin Usage page.
 *
 * @returns The page.
 */
export default function AdminUsagePage() {
  return (
    <>
      <AdminPageHeader
        title="Usage"
        lead="Tokens, messages and web searches per User per day. Counts only."
      />
      <AdminUsage />
    </>
  );
}
