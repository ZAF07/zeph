import { redirect } from "next/navigation";

/**
 * The admin area's front door, which opens the Users page.
 *
 * @returns Nothing; it always redirects.
 */
export default function AdminPage() {
  redirect("/admin/users");
}
