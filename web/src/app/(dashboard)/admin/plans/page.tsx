import { AdminPageHeader } from "@/components/AdminPageHeader";
import { EmptyState } from "@/components/EmptyState";
import { ToBuildTag } from "@/components/ToBuildTag";

/**
 * The admin Plans page. Plans have no backend or design yet, so it shows
 * the "To build" empty state.
 *
 * @returns The page.
 */
export default function AdminPlansPage() {
  return (
    <>
      <AdminPageHeader
        title={
          <>
            Plans
            <ToBuildTag />
          </>
        }
        lead="The plans Users can choose and what each includes."
      />
      <EmptyState
        title="No plans yet"
        body="Plans and billing aren’t built yet. This page will list them once they are."
      />
    </>
  );
}
