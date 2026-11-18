import { menuLinkHover } from "@/components/menu-styles";

/**
 * The small underlined link inside a card, such as "Manage connection" or
 * "Review all", at least 44px tall.
 */
export const cardLink = `inline-flex min-h-11 items-center text-[13px] text-text underline ${menuLinkHover}`;

/** A small rounded status label, like "On" or "No reply". */
export const statusPill =
  "rounded-pill px-2.5 py-0.5 text-[12px] font-normal whitespace-nowrap";
