/**
 * Class names for the pill buttons on the design's `States` sheet. While a
 * button is disabled (for example "Saving…") it takes the drawn working look.
 */
const base =
  "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-pill border px-[22px] text-[14px] font-medium no-underline disabled:cursor-not-allowed disabled:border-line-strong disabled:bg-transparent disabled:text-mute";

/** The one main action on a view. Keeps its ink text on hover when a link. */
export const primaryButton = `${base} border-cream bg-cream text-ink hover:text-ink`;

/** A secondary action. */
export const secondaryButton = `${base} border-soft bg-transparent text-text`;

/** A small secondary action inside a table row. */
export const compactSecondaryButton =
  "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-pill border border-line-strong bg-transparent px-3.5 text-[13px] font-medium whitespace-nowrap text-text disabled:cursor-not-allowed disabled:text-mute";

/**
 * An action inside an admin table row, drawn as the Users page's "Manage":
 * small underlined text.
 */
export const rowActionButton =
  "inline-flex min-h-11 cursor-pointer items-center border-0 bg-transparent p-0 font-[inherit] text-[13px] text-text underline hover:text-cream disabled:cursor-not-allowed disabled:text-mute";

/** A destructive action. Keeps its colour on hover when a link. */
export const dangerButton = `${base} border-danger bg-transparent text-danger hover:text-danger`;

/**
 * The button that confirms a destructive action. The design draws it the
 * same as `dangerButton`.
 */
export const confirmDangerButton = dangerButton;

/** An icon-only delete button inside a card or list row. */
export const deleteIconButton =
  "inline-flex size-11 flex-none cursor-pointer items-center justify-center rounded-input border-0 bg-transparent p-0 text-soft disabled:cursor-not-allowed disabled:opacity-60";
