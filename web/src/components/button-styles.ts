/** Class names for the button styles on the Foundations screen. */
const base =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-[22px] py-3 text-[15px] font-medium leading-tight whitespace-nowrap no-underline cursor-pointer";

/** The one main action on a view. */
export const primaryButton = `${base} border border-ink bg-ink text-white hover:text-white disabled:cursor-not-allowed disabled:border-line-strong disabled:bg-line-strong disabled:text-ink-muted`;

/** A secondary action. */
export const secondaryButton = `${base} border border-line-strong bg-transparent text-ink disabled:cursor-not-allowed disabled:opacity-60`;

/** A quiet, link-like action. */
export const quietButton = `${base} border border-transparent bg-transparent px-2 text-blue`;

/** A small secondary action inside a table row. */
export const compactSecondaryButton =
  "inline-flex min-h-10 items-center justify-center whitespace-nowrap rounded-full border border-line-strong bg-transparent px-3.5 py-2 text-sm font-medium leading-tight text-ink cursor-pointer disabled:cursor-not-allowed disabled:opacity-60";
