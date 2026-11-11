/** Class names for the button styles on the Foundations screen. */
const base =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-[22px] py-3 text-[15px] font-medium leading-tight whitespace-nowrap no-underline cursor-pointer";

/** The one main action on a view. */
export const primaryButton = `${base} border border-ink bg-ink text-white hover:text-white`;

/** A secondary action. */
export const secondaryButton = `${base} border border-line-strong bg-transparent text-ink`;

/** A quiet, link-like action. */
export const quietButton = `${base} border border-transparent bg-transparent px-2 text-blue`;
