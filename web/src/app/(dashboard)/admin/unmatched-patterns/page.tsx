import { AdminPageHeader } from "@/components/AdminPageHeader";
import { UnmatchedPatternsManager } from "@/components/UnmatchedPatternsManager";

/**
 * The admin Unmatched Patterns page: what Zeph keeps noticing that fits no
 * Pattern Type, for Admins to decide what the catalog should gain.
 *
 * @returns The page.
 */
export default function AdminUnmatchedPatternsPage() {
  return (
    <>
      <AdminPageHeader
        title="Unmatched Patterns"
        lead="What Zeph keeps noticing that fits no Pattern Type, so the catalog can grow. Each entry is a general description with nothing about a User, and how many Users it appears for. Mark each one: a new Pattern Type, folded into one, or dropped."
      />
      <UnmatchedPatternsManager />
    </>
  );
}
