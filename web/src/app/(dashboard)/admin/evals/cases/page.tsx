import { redirect } from "next/navigation";

/**
 * The Eval Cases page opens the first Eval's cases.
 *
 * @returns Nothing; it redirects.
 */
export default function AdminEvalCasesPage() {
  redirect("/admin/evals/cases/safeguard");
}
