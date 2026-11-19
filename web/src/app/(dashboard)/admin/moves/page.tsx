import { AdminPageHeader } from "@/components/AdminPageHeader";
import { MovesManager } from "@/components/MovesManager";

/**
 * The admin Moves page: what Zeph does to help in a reply.
 *
 * @returns The page.
 */
export default function AdminMovesPage() {
  return (
    <>
      <AdminPageHeader
        title="Moves"
        lead="What Zeph does to help in a reply. Before each reply, Zeph picks a lead Move and at most one supporting Move from those the Need allows, reading each “when it fits”, then follows their “how to do it”. A Move that needs a Feature is never offered when that Feature doesn’t work for the User. Changes apply to the next Message."
      />
      <MovesManager />
    </>
  );
}
