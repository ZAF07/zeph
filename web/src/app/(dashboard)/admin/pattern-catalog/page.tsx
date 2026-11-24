import { AdminPageHeader } from "@/components/AdminPageHeader";
import { PatternCatalog } from "@/components/PatternCatalog";

/**
 * The admin Pattern Catalog page.
 *
 * @returns The page.
 */
export default function AdminPatternCatalogPage() {
  return (
    <>
      <AdminPageHeader
        title="Pattern Catalog"
        lead="One card per Pattern Type: what Zeph may look for in what a User says, and how it may word it."
      />
      <PatternCatalog />
    </>
  );
}
