import { menuLinkHover } from "@/components/menu-styles";

/**
 * The small underlined link inside a card, such as "Manage connection" or
 * "Review all", at least 44px tall.
 */
export const cardLink = `inline-flex min-h-11 items-center text-[13px] text-text underline ${menuLinkHover}`;

/** One row of a card's list, with a line above every row but the first. */
export const cardListRow =
  "flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-t border-line py-3 first:border-t-0";

/** The main panel card, as the Connect Telegram card is drawn. */
export const panelCard =
  "box-border rounded-card border border-line bg-panel px-7 py-[26px]";

const pillBase =
  "rounded-pill px-2.5 py-0.5 text-[12px] font-normal whitespace-nowrap";

/** The cream status pill for a state worth noticing, like "On" or "Replied". */
export const filledPill = `${pillBase} bg-cream text-ink`;

/** The outlined status pill for any other state, like "Off" or "No reply". */
export const outlinedPill = `${pillBase} border border-line-strong text-soft`;
