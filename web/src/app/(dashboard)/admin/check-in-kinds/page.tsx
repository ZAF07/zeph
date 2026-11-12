import { AdminPageHeader } from "@/components/AdminPageHeader";
import { CheckInKindsManager } from "@/components/CheckInKindsManager";

/**
 * The admin Check-in Kinds page: the kinds of message Zeph may start.
 *
 * @returns The page.
 */
export default function AdminCheckInKindsPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Check-in Kinds"
        lead="The kinds of message Zeph may start. The Check-ins service reads each description to choose one — or to skip. Users see the names, read-only."
      />
      <CheckInKindsManager />
    </div>
  );
}
