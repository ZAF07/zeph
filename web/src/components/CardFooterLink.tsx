import Link from "next/link";

import { cardLink } from "@/components/card-styles";

/**
 * The link at the foot of a card's list, below a dividing line, such as
 * "Open Features" on the admin Overview.
 *
 * @param props - `href` is where it goes; `label` is its text.
 * @returns The link row.
 */
export function CardFooterLink({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  return (
    <div className="border-t border-line">
      <Link href={href} className={cardLink}>
        {label}
      </Link>
    </div>
  );
}
