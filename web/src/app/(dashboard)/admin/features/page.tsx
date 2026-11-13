import { AdminFeatures } from "@/components/AdminFeatures";
import { AdminPageHeader } from "@/components/AdminPageHeader";

/**
 * The admin Features page.
 *
 * @returns The page.
 */
export default function AdminFeaturesPage() {
  return (
    <div className="flex max-w-[920px] flex-col gap-[30px]">
      <AdminPageHeader
        title="Features"
        lead="What Zeph offers. Turn a Feature off for everyone and it stops at the next message; nothing is deleted. Safety and Users’ own data are never switched off."
      />
      <AdminFeatures />
    </div>
  );
}
