import { AdminPageHeader } from "@/components/AdminPageHeader";
import { ModelCallLog } from "@/components/ModelCallLog";

/**
 * The admin Model Call Log page.
 *
 * @returns The page.
 */
export default function AdminModelCallLogPage() {
  return (
    <>
      <AdminPageHeader
        title="Model call log"
        lead="Every model call the Companion made, one trace per Message, Check-in or Conversation end. Content only for Admins’ own chats and Evals."
      />
      <ModelCallLog />
    </>
  );
}
