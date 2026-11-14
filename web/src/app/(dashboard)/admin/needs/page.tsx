import { AdminPageHeader } from "@/components/AdminPageHeader";
import { NeedsManager } from "@/components/NeedsManager";

/**
 * The admin Needs page: what a User may want from Zeph right now.
 *
 * @returns The page.
 */
export default function AdminNeedsPage() {
  return (
    <div className="flex flex-col gap-[30px]">
      <AdminPageHeader
        title="Needs"
        lead="What a User may want from Zeph right now. Before each reply, Zeph reads every “when it fits” to pick one, then follows its “how to reply”. Changes apply to the next Message. The fallback is used when it isn’t clear."
      />
      <NeedsManager />
    </div>
  );
}
