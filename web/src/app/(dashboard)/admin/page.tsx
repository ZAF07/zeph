import { AdminOverview } from "@/components/AdminOverview";
import { overviewSample } from "@/lib/design-fixtures/overview";

/**
 * The admin area's front door, the Overview. Its counts have no backend
 * yet, so it shows the drawn sample values and makes no backend calls.
 *
 * @returns The page.
 */
export default function AdminPage() {
  return <AdminOverview overview={overviewSample} />;
}
