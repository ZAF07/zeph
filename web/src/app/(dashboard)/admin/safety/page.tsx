import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CrisisReplyEditor } from "@/components/CrisisReplyEditor";
import { HelplinesManager } from "@/components/HelplinesManager";

/**
 * The admin Safety page: the Crisis Reply wording and the Helplines it
 * shares.
 *
 * @returns The page.
 */
export default function AdminSafetyPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Safety"
        lead="What Zeph says when Safeguard detects risk, and the Helplines it shares for each User’s country."
      />
      <CrisisReplyEditor />
      <HelplinesManager />
    </div>
  );
}
