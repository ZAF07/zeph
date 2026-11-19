import { AdminPageHeader } from "@/components/AdminPageHeader";
import { SafeguardEvents } from "@/components/SafeguardEvents";

/**
 * The admin Safeguard Events page.
 *
 * @returns The page.
 */
export default function AdminSafeguardEventsPage() {
  return (
    <>
      <AdminPageHeader
        title="Safeguard Events"
        lead="Each time Safeguard detected risk and sent the Crisis Reply. Who and when only — never what was said."
      />
      <SafeguardEvents />
    </>
  );
}
