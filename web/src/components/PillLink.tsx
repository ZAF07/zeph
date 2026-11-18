import Link from "next/link";

import { primaryButton, secondaryButton } from "@/components/button-styles";

/**
 * A pill-shaped link to the next step, ending in an arrow.
 *
 * @param props - `href` is where it goes, `label` its text, and `primary`
 *   makes it the cream main action instead of the outlined one.
 * @returns The link.
 */
export function PillLink({
  href,
  label,
  primary = false,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  return (
    <Link href={href} className={primary ? primaryButton : secondaryButton}>
      {label}{" "}
      <span aria-hidden="true" className="ml-2.5">
        →
      </span>
    </Link>
  );
}
